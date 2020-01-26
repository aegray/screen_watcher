# screen_watcher

I am a heavy user of screen, often having upwards of 100 different windows (organized by 
multiple levels of running screen).  A common problem I have is that it's easy to context switch
and lose track of or forget about long running commands or where I was working on something.

This acts as a screen "monitor" that displays the process tree of screens and running commands 
under them as a tree.  Under each window, it shows information both about the current running 
command and previously finished commands, color coded based on their return value.


To setup:

```mkdir -p ~/utils/cmdstat```

Add to your ~/.bashrc:
```
function update_cmdstat() {
    exitcode=$?
    echo "$(history 1) : $exitcode" > ~/utils/cmdstat/stat.$$ 
    return "$exitcode"
}

export PROMPT_COMMAND=' $( update_cmdstat ) '

```

And run ./watch_screens.sh


