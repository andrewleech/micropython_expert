The inbuilt LCD driver has a number of functions defining its behaviour:

```python
lcd.clear()     # clears the ecreen
lcd.reset(x,y)  # clears the pixel at x,y to a 0 or empty state
lcd.set(x,y)    # sets the pixel on at position x,y
lcd.get(x,y)    # returns a 0 or 1 indicating the off/on state of the pixel at x,y
lcd.show()      # updates the display and forces a redraw.
```
!!how do we set the mode for a given lcd device.
!! if its byte mapped instead of pixel mapped what do we get back from a get()

Example:
```
lcd.clear()
```