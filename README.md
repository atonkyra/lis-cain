```
    on commit {
        set clip = binary-to-ascii(10, 8, ".", leased-address);
        set swmac = pick-first-value(binary-to-ascii(16, 8,":",suffix(option agent.remote-id, 6)), "");
        set swport = pick-first-value(binary-to-ascii (10, 8, "/", suffix(option agent.circuit-id, 2)), "");
        execute("/opt/lis-cain/dhcp-hook.py", clip, swmac, swport);
    }
```
