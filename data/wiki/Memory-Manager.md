## Implementation
The current memory manager is in `py/gc.c` and is almost a textbook implementation of mark-sweep GC.

Resources:
- wikipedia article on [Trace/sweep garbage collection](http://en.wikipedia.org/wiki/Tracing_garbage_collection)

## Wishlist
- [Eliminate heap-memory fragmentation](http://forum.micropython.org/viewtopic.php?f=3&t=455)

When running for an extended period of time (usually after allocating large buffers), the heap can become very fragmented, and although there is enough free memory for an allocation, the free memory is not contiguous (all in a row). Such a problem severely limits uPy's use in critical and long-running applications (eg a web server, a quadcopter). Code running on a microcontroller needs to be a lot more robust than desktop software running on a PC, and so special care must be taken to design a robust memory allocator.

It's not clear how to improve uPy's current memory allocator so that fragmentation is reduced. Ultimately I would want to see a solution that completely eliminates fragmentation, so that programs are guaranteed to run indefinitely. Note that heap fragmentation is not because of the use of garbage collection: even with reference counting, or explicit free, you still have the same amount of fragmentation. The 2 ideas I have to eliminate fragmentation are: 1) a copying memory manager/garbage collector, that can move parts of the heap around so as to make contiguous regions available; 2) a fixed-block memory manager than allocates a single block size (eg 16 bytes), and if you want more you must chain multiple blocks (like a filesystem). Both of these ideas are difficult to implement, and will come with a speed and memory cost. But the cost will be worth it if we can get guaranteed memory allocation.

# `py/gc.c` File documentation
## User Level Functions
The main functions that a user needs are:
* `gc_init`: initialize the memory manager (called once on startup)
* `gc_alloc`: malloc with gc
* `gc_free`: free with gc
* `gc_realloc`: realloc with gc

## Memory structure

### Glossary

| Name | Definition |
| ---- | ---------- |
| ATB  | Allocation table byte, contains allocation status of 4 blocks.
| allocation table | Array of ATB's that describes the current state (free, head, tail, mark).
| block | Basic unit of storage for the GC, currently 16 bytes. Indexed by the `size_t` block number (usually just called "block" as well).
| finalizer table | List of bits indicating whether the given block has a finalizer.
| FTB  | Finalizer table byte, contains finalizer bits of 8 blocks.
| pool | Allocatable memory, divided in a list of blocks.

### Initialisation

On startup, MicroPython initialises the GC with the `gc_init(start, end)` call, which takes a start and end pointer. This function is called from a port-specific `main()` so how this memory is obtained is port-specific (either via `malloc()` or by a large statically allocated buffer).

This memory is subdivided in three parts, the alloc table, the finalizer table, and the memory pool itself:

| area             | storage |
| ---------------- | ------- |
| allocation table | 2 bits per block, thus manages 4 blocks per byte
| finalizer table  | 1 bit per block, thus manages 8 bits per byte (optional)
| pool             | allocatable storage

### Allocation table entries

Every block has a 2-bit allocation status attached to it, as stored in the allocation table.

| bits   | meaning |
| ------ | ------- |
| `0b00` | FREE: free block
| `0b01` | HEAD: head of a chain of block
| `0b10` | TAIL: in the tail of a chain of blocks
| `0b11` | MARK: marked head block

Blocks are managed as follows:

* Initially, all blocks are marked _free_ (by zeroing the allocation table).
* When a block is allocated, the GC tries to find a contiguous range of blocks that are free, big enough for the requested amount of memory (rounded up to a block boundary). The first block is set to _head_ and all following blocks (if there are any) are set to _tail_.
* Within a GC cycle, reachable head blocks are set to _mark_. Unreachable blocks will stay as _head_ and be freed. After the GC cycle, marked blocks are again set to head.
* When a block is freed (which must be a head block), this block and all following tail blocks are set to free. Additionally, if the bit in the finaliser table for this block is set (see `FTB_SET`), call the finaliser for this object if there is any.

### Garbage collection cycle

The garbage collector is triggered either explicitly, or automatically when there is no free memory left during an allocation.

The garbage collector has a few phases:

* Collect all root pointers by marking those blocks (see `gc_collect_start` and `gc_collect_root`).
* Mark phase: scan the memory, until all marked blocks don't reference unmarked blocks anymore (meaning every reachable block is marked). See `gc_deal_with_stack_overflow` (called in `gc_collect_end`).
* Sweep phase: go through all blocks in the allocation table, whereby unmarked blocks are freed and marked blocks are set to unmarked. Blocks are never set to 'mark' outside of a GC cycle. See `gc_sweep` (called in `gc_collect_end`).

The `gc_collect` function itself is implemented per port, so that it can easily be customized to mark all root pointers. Usually it is very short, mostly calling the above functions and perhaps adding a few more root pointers.

### Pseudocode

The Python pseudocode of the garbage collector (mark and sweep) would be the following:

```python
gc.stack_overflow = False
gc.stack = [] # array of blocks that are marked but not their children
gc.memory = ... # list of all blocks managed by the memory manager

MICROPY_ALLOC_GC_STACK_SIZE = 64 # default stack size (see py/mpconfig.h)

def gc_collect(): # implemented by ports
  # add root pointers (platform-dependent)
  gc_collect_root(roots)

  # if there was a stack overflow, scan all memory for reachable blocks
  gc_deal_with_stack_overflow()

  # free all unreachable blocks
  gc_sweep()

def gc_collect_root(roots):
  for root in roots:
    # Test whether this could be a pointer.
    if looks_like_pointer(root):
      block = block_from_ptr(root)
      if block.state == HEAD:
        # Set the mark bit on this block.
        block.state = MARK

        # Mark all descendants of this root.
        gc_mark_subtree(block)

def gc_mark_subtree(block):
  # The passed in block must already been marked.

  # Try to reduce the stack, and don't return until it's empty. But with every
  # reduction, multiple blocks may be added to the stack so this function may
  # actually hit a stack overflow.
  while True:
    # Check this block's children.
    # Each block contains 4 memory words (on a 32-bit system with 16-byte
    # blocks). These words may be pointers to blocks on the heap, but may also
    # be other things like integers, parts of raw data (strings, bytecode, etc.)
    # or pointers to memory outside of the heap.
    for pointer in reversed(block.all_pointers_in_chain()[1:]):
      if looks_like_pointer(pointer):
        childblock = block_from_ptr(pointer)
        if childblock.state == HEAD:
          childblock.state = MARK
          # Is there space left on the GC stack?
          if len(gc.stack) < MICROPY_ALLOC_GC_STACK_SIZE:
            # Yes, add this block to the stack.
            gc.stack.append(block)
          else:
            # Sadly, no. The mark phase can continue, but the whole memory will need
            # to be scanned again (some marked blocks may have unmarked children).
            gc.stack_overflow = True

    # Are there any blocks on the stack?
    if len(gc.stack) == 0:
      break # No, stack is empty, we're done.

    # pop the next block off the stack
    block = gc.stack.pop()

def gc_deal_with_stack_overflow():
  # Keep scanning the whole memory until all marked blocks don't have unmarked
  # children.
  # A 'stack overflow' happens if the GC stack cannot contain any more items.
  # The stack is there to make the mark phase more efficient, i.e. it avoids
  # having to scan the whole memory too often. But sometimes, the stack is too
  # small and requires a full scan (like at the beginning of the mark phase).
  while gc.stack_overflow:
    gc.stack_overflow = False
    for block in gc.memory:
      # A block can have the states FREE, HEAD, TAIL or MARK, as set in the
      # allocation table.
      if block.state == MARK:
        gc_mark_subtree(block)

def gc_sweep():
  # Free unmarked blocks and unmark marked blocks.
  free_tail = False
  for block in gc.memory:
    if block.state == HEAD:
      block.state = FREE
      free_tail = True
    elif block.state == TAIL:
      if free_tail:
        block.state = FREE
    elif block.state == MARK:
      block.state = HEAD
      free_tail = False
```

### Macros

The memory manager uses many macros, which may not be obvious at first:

* `ATB_n_IS_FREE(a)`: Check whether, in a given allocation table byte, the `n`th entry is free. There are currently 4 entries per byte (0-3). The only place where this macro is used, is in `gc_alloc` to find a contiguous range of free blocks.
* `ATB_GET_KIND(block)`, `ATB_ANY_TO_FREE(block)`, `ATB_x_TO_y(block)`: Get allocation status of a block and manipulate the allocation table. Used throughout the memory manager.
* `BLOCK_FROM_PTR(ptr)`: Get the block number of a pointer.
* `PTR_FROM_BLOCK(block)`: Get a pointer from a block number (inverse of `BLOCK_FROM_PTR`).
* `ATB_FROM_BLOCK(block)`: Not currently used.
* `FTB_GET(block)`, `FTB_SET(block)`, `FTB_CLEAR(block)`: Manage the finaliser bit for a given block.