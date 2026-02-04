These guidelines are here to help you write a driver (library for a component) with an API that is as portable between different platforms that run Micropython as possible, while at the same time being easy to learn to use, consistent with other drivers, and efficient.

Don't create Pin/SPI/I2C/UART/etc. objects in your driver
---------------------------------------------------------

Instead of creating all the objects that specify how your driver talks to the component and where the component is connected, simply let the user create them and pass in the constructor or a call to the initialization method. This way the users have greater freedom of choice, and your driver will work across different platforms where those objects are created differently.

Avoid using properties
----------------------

While properties are a very powerful feature of the language, in Micropython they are pretty wasteful in terms of resources. It's also a bad practice to use properties for actions that have side effects. Therefore, for drivers (which usually have side effects, that's the whole point of them) use methods instead. The pattern is as follows:

```
def register(self, value=None):
    if value is None:
        return self._register
    self._register = value
    # do something...
```

This way you can call this method without parameters to get the current value, or with a parameter to set it.

Keep names consistent with other drivers
----------------------------------------

Look for existing drivers doing a similar thing to what your does, and try to keep the same names for the methods. For instance, if you are writing a driver for a display, keep the API similar to the SSD1306 library in Micropython's repository. If you can't find a similar library, spend some time thinking about the names -- you are setting a standard here. Possibly discuss the API on the forum.

Allow re-initialization of objects without their re-creation
------------------------------------------------------------

Have an `init` method that takes the same parameters as the constructor, but changes the existing object instead of creating a new one. Object creation is relatively costly in Micropython and it's good to have a way of avoiding it.

Avoid Error Return Values
-------------------------

Instead of returning None, -1 or NaN when something goes wrong, simply raise an exception. This makes it much easier to debug programs, and results in a cleaner code (not having to add those ifs every time you use a value). But keep in mind that handling exception is relatively expensive operation, so for low-level operations which used a lot by other code, e.g. tight loops, it may be better to return error code instead.

Provide Raw Sensor Readings
---------------------------

If you do some computations to convert sensor readings into the right units and generally make it friendlier for the user, remember to leave an option of getting the raw values that you got from the sensor (for instance, by passing `raw=True`). This will make debugging much easier, and will let the user to use those values in ways that you didn't anticipate.