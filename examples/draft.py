import time

import ltstatus.monitor as m

sound_aliases = {
    "iFi (by AMR) HD USB Audio Pro": "ifi",
    "apm.zero": "apm",
    "Dummy Output": "none",
}

# TODO add here what pid stats does? up to custom to pass arguments, use dev as with other stuff for editing?
# still need ltstatus to make it importable? or just put all things i want in ltstatus directly?
# TODO actually, ltstatus here looks like its not using much cpu, but pid stats seems quite heavy after all
# or just make it on demand, if i see overall usage is heavy
# or have a tmux popup to give me a nice ncdu like thing snapshot when i need to see it?

with (
    m.cpu() as cpu,
    m.nvidia() as nvidia,
    m.bluetooth() as bluetooth,
    m.sound(sound_aliases) as sound,
    m.redshift() as redshift,
    m.datetime() as datetime,
):
    while True:
        time.sleep(1)
        print(
            f"{cpu()} | {nvidia()} | {bluetooth()} | {sound()} | {redshift()} | {datetime()}",
            flush=True,
        )
