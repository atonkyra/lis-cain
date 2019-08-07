# lis-cain

## tftpy
lis-cain requires custom tftpy which you can clone from https://github.com/atonkyra/tftpy.git

## isc-dhcp-server
```
    on commit {
        set clip = binary-to-ascii(10, 8, ".", leased-address);
        set swmac = pick-first-value(binary-to-ascii(16, 8,":",suffix(option agent.remote-id, 6)), "");
        set swport = pick-first-value(binary-to-ascii (10, 8, "/", suffix(option agent.circuit-id, 2)), "");
        execute("/opt/lis-cain/dhcp-hook.py", clip, swmac, swport);
    }
```

## port-channel generator
```
usage: portchan.py [-h] -p PREFIX [-f FIRST] [-m MODE] [-d DISTSW]

optional arguments:
  -h, --help            show this help message and exit
  -p PREFIX, --prefix PREFIX
  -f FIRST, --first FIRST
  -m MODE, --mode MODE
  -d DISTSW, --distsw DISTSW
```

#### --prefix
Prefix for distribution switch ports. Can be given in format "Gi" or "Gi0".  
Choosing "Gi" takes module number from port configuration. In case of fixed-configuration switches, we usually want to override it to "Gi0" or "Gi1/0"

#### --first
Number of first port-channel interface. Defaults to 5 leaving four free for core connections.

#### --mode
Operating mode e.g. active or desirable

#### --distsw
Specify distribution switches. Can be used 0, 1 or more times. Without using this all configs are generated.  
Useful when dealing with different switches in distribution layer.  
Just run once with most common settings and afterwards use this option to overwrite different settings.
