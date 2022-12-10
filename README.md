# grony

An utility to schedule git-related actions (`pull`, `commit` and `push` at this moment) using crontab expressions.

## Installation

> Note: you need Python 3.

```sh
> pip install grony
```

After that, should have a `grony` command available.

```sh
> grony
```

## Usage

`grony` consists of two components:

- A long running process (the scheduler) used to schedule and launch git commands.
- A client, used to manage the scheduler.

First things first. You need to start the scheduler.

## Starting the scheduler

Using whatever method you want (in a console, a startup script o anything supported in your OS) run:

```sh
> grony start
```

The tool will run in foreground. So it's advised yo use a way to leave it as a background process.

### Starting the scheduler as a service in Linux

TBD.

### Starting the scheduler as a service in macOS

Use the scripts located at `scripts/macOS` in this repo to add/remove a launchd for grony.

To enable the grony scheduler as a service and start automatically when the current user logs in.

```sh
> scripts/macOS/add-launchd.sh
```

To prevent the grony scheduler to start automatically when the current user logs in.

```sh
> scripts/macOS/remove-launchd.sh
```

## Add a repository

Say you want to execute an automatic commit on a repository located at `/sources/my-project`.

```sh
> grony add /sources/my-project
Repository friendly name [my-project]: <press enter>
Successfully added my-project
```

That's it. That command instructs grony to schedule tasks for that repository. No to the next ste.

## Configure actions

You need a way to tell grony what commands to run and when. Depending of your needs or personal preferences, you can use two ways:

- A centralized one, configured in (whichever is found first):
  - `$GRONY_CONFIG_PATH`
  - `$XDG_CONFIG_HOME/.grony/grony.conf`
  - `$HOME/.grony/grony.conf`.
- A decentralized one, configured in each repo's `.grony` file.

### Configuring actions in `grony.conf`

Open your `grony.conf` in a text editor. You should see something like this (you can ignore any value in the `[config]` section as it's used internally by the program)

```ini
[config]
ipc_port = 62830
secret = 4ac19f9d-7e18-4a0e-aa83-729c51bdddcf

[repo 'my-project']
path = /sources/my-project
```

You must setup what to do in `my-project` in the section `[repo 'my-project']`.

Available options are:

- `pull-on`: a crontab-like expression detailing when to run `git pull`.
- `pull-remote`: the remote name where to pull from (optional)
- `commit-on`: a crontab-like expression detailing when to run `git add -A && git commit`.
- `commit-message`: the commit message for `commit-on` (defaults to 'Auto commit at %Y%m%d %H:%M:%S').
- `push-on`: : a crontab-like expression detailing when to run `git push`.
- `push-remote`: the remote name where to push to (optional)

You don't have to set all values. Only those what you need. For example, if you only need to perform automatic commits every minute and you are ok with the default message, configure `commit-on` like this:

```ini
[repo 'my-project']
path = /sources/my-project
commit-on = * * * * *
```

You can configure all actions if you want. Remember that if they need to run at the same time, they'll run always in the this order: `pull-on`, `commit-on`, `push-on`.

```ini
[repo 'my-project']
path = /sources/my-project
push-on = @hourly         ; the config order you use does not matter
pull-on = @hourly
commit-on = @hourly
```

### Configuring actions in each repo's `.grony`

You can put a `.grony` file in the repository root with the following format:

```ini
[repo]
push-on = @hourly
pull-on = @hourly
commit-on = @hourly
```

Note:

- It does not contain a `[config]` section.
- The section is called `[repo]`.
- It does not contain the repository `path`.

Outside of that, the settings are exactly the same.

You can use the following command to initialize a basic `.grony` file with default settings in a repository root:

```sh
> grony init /sources/my-project
```

### Overriding `.grony` settings

You can have settings for a repo defined both in the `.grony` file and in your `grony.conf`.

Both settings will be merged at run time and any setting present in `grony.conf` **will override** the one in the `.grony` file.

> This is useful to override some settings on a per-machine basis, like the commit message, for example.

### Updating settings

You can update any setting in any moment. grony will reload all files periodically to update the scheduled tasks.

> Note: this interval can be user-defined in `grony start` (see below).

## More info

Just use the integrated help for the rest of the commands. It's pretty self-explanatory.

```
Usage: grony [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  add     Adds a repository to the grony.conf file.
  init    Initializes a .grony file in the specified path.
  list    List all configured repositories.
  remove  Removes a repository from the grony.conf file.
  show    Show the effeective settings for a repository.
  start   Starts the main process.
```
