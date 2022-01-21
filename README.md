![Image of Bubbles, from 1998's Powerpuff Girls](https://i.imgur.com/6MfNGdy.png)

<h1 align="center">bubbles</h1>

<p align="center">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

This is the modchat chatbot! Bubbles started out on the [errbot](https://github.com/errbotio/errbot) platform before migrating to a complete rewrite around the new SlackClient.

## Development

Start by making sure that you have [poetry](https://python-poetry.org/) installed, then create the virtual environment.

```shell script
# create the virtual environment
poetry install

# activate the environment
poetry shell
```

You may need a .env file for secrets -- copy `.env-example` to `.env` and fill it out. If you're testing in your own slack instance, [create a bot token here](https://my.slack.com/services/new/bot).

If you're testing commands locally that do not need to access to advanced functionality (external services, mostly), you can invoke the interactive terminal by running:

```shell script
python bubblesRTM.py --interactive
```

This will create a shell session where you can test commands without needing to be hooked up to anything special.

## Adding Commands

Bubbles uses a plugin manager to register commands. Each command is registered inside the command file, and each command should only need one file.

### Example Command

```python
from bubbles.config import PluginManager


def hello_world(rtmclient, client, user_list, data):
    return client.chat_postMessage(
        channel=data.get("channel"), text="Hello, world!", as_user=True
    )


PluginManager.register_plugin(hello_world, r"hello")
```

The above plugin will post "Hello, world!" to the channel you message Bubbles from with the following any of the following syntax:

```
!hello
@bubbles hello
bubbles hello
```

If you want to write a command that doesn't need the prefix to trigger, just add the `ignore_prefix=True` into the register command.

```python
PluginManager.register_plugin(hello_world, r"hello", ignore_prefix=True)
```

Now it will trigger any time that the word "hello" is put into chat. `register_plugin` can handle a few more edge cases as well:

`flags`: used for combining `re` compilation flags for regex. For example:

```python
PluginManager.register_plugin(hello_world, r"hello", flags=re.IGNORECASE | re.MULTILINE)
```

`callback`: if you need to keep track of messages, a command callback can be called on every message. To see an example of this in action (and using a class structure for a plugin), take a look at `bubbles/commands/yell.py`.

## Running the bot

```shell script
python bubblesRTM.py
```
