
# git-tracker

Keep track of your private and public git activity.

Two different kinds of charts are provided to visualize your git activity: a [heat map](http://en.wikipedia.org/wiki/Heat_map) and a [tree map](http://en.wikipedia.org/wiki/Treemapping).

To use, you must have a machine ssh key (e.g., a ssh key that is not pass-phrase protected and has read-only access to your repositories).

Currently the backend consists of a [Flask](http://flask.pocoo.org/) app in conjunction with [pygit2](https://github.com/libgit2/pygit2). Git activity is matched via email address, and in the event you commit under different email addresses, you can add these email addresses to your user account for comprehensive git activity matching.

This is mostly feature complete but not quite where I want it to be: in particular, it is still lacking PR support, date range handling, and a more versatile front-end (currently in ES6 javascript). Docker support is also planned.
