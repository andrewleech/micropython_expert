## Using `network.PPP` to connect to a Linux host over USB UART.

This is useful for testing the PPP driver.

With a USB UART available as /dev/ttyUSB1 connected to pins (e.g.) 5,22,18,21 on the device:

```bash
$ sudo pppd nodetach noauth crtscts lock proxyarp 192.168.150.1:192.168.150.2 /dev/ttyUSB1 115200
```

Then on the device:

```py
import machine, network

u = machine.UART(1, baudrate=115200, tx=5, rx=22, cts=18, rts=21, flow=3)
p = network.PPP(u)
p.active(1)
p.connect()
```

On success, `pppd` will print out

```
Using interface ppp0
Connect: ppp0 <--> /dev/ttyUSB1
local  LL address fe80::ad92:0d2c:01a6:4e6d
remote LL address fe80::2d30:5ecb:8702:97ba
local  IP address 192.168.150.1
remote IP address 129.168.150.2
```

## Authentication

To enable authentication, change `noauth` to `auth servername` and add an entry to `/etc/ppp/pap-secrets:

```
user servername pass 192.168.150.2
```

Then pass the authentication details to `connect`:

```py
p.connect(authmode=p.AUTH_PAP, username="user", password="pass")
```