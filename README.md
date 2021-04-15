# umeboshi

```
  __    __                          __                            __        __ 
  /  |  /  |                        /  |                          /  |      /  |
  $$ |  $$ | _____  ____    ______  $$ |____    ______    _______ $$ |____  $$/ 
  $$ |  $$ |/     \/    \  /      \ $$      \  /      \  /       |$$      \ /  |
  $$ |  $$ |$$$$$$ $$$$  |/$$$$$$  |$$$$$$$  |/$$$$$$  |/$$$$$$$/ $$$$$$$  |$$ |
  $$ |  $$ |$$ | $$ | $$ |$$    $$ |$$ |  $$ |$$ |  $$ |$$      \ $$ |  $$ |$$ |
  $$ \__$$ |$$ | $$ | $$ |$$$$$$$$/ $$ |__$$ |$$ \__$$ | $$$$$$  |$$ |  $$ |$$ |
  $$    $$/ $$ | $$ | $$ |$$       |$$    $$/ $$    $$/ /     $$/ $$ |  $$ |$$ |
   $$$$$$/  $$/  $$/  $$/  $$$$$$$/ $$$$$$$/   $$$$$$/  $$$$$$$/  $$/   $$/ $$/ 
```

Umeboshi is a [Django][django] application for durable long-term scheduling of arbitrary actions.

[django]: https://www.djangoproject.com/

# What you need

You need a flexible, generalized way to schedule future computation in your Django app.

Great! You should use [celery][].

Ah, but: you do use celery, and you love it, but you have it hooked up to a messaging/queuing protocol like AMQP, backed by an in-memory service like RabbitMQ. RabbitMQ is great for dispatching messages that you expect to be consumed some time within the next few minutes. But some of the computation you want to schedule needs to sit on the wire for days---maybe even months---and you don't feel comfortable dumping it into a queue.

[celery]: http://www.celeryproject.org/

## Ok, then you should try Umeboshi

Umeboshi is a new, lightweight system for scheduling computation with a higher level of persistence than queue-backed solutions. Umeboshi saves your tasks to the database, and runs them later. 

# How it works, roughly

Umeboshi contains only two basic concepts: **Routines** and **Events**. **Routines** are classes that you write that do things in a `run()` method. Then, in your code, schedule a Routine to be run at a certain time, with certain arguments. Umeboshi will then save an **Event** to the database with information in it. When the time you specified comes up, Umeboshi will grab your Routine and run it.

# An example

Let's say you rent jetskis. You've got a JetSki model in your Django application with a `out_for_rent` field. You're highly successful because you charge your customers a one-time \$600 fee if they hold on to your jetskis for more than 30 days. You use Umeboshi to help you enrich yourself on your watersports-loving (but forgetful) clientele. 

```python
from umeboshi.routines import routine

@routine
class JetSkiLateFee(object):

	# Umeboshi saves its Events to the db with a trigger name that corresponds
	# to the Routine to be run when they're ready.
	trigger_name = 'ski-late-fee'

    def __init__(self, jetski_id, user_id):
        # When a Event is scheduled to be run, it is instantiated with the
        # arguments it was saved with. In this case it was saved with two
        # integer arguments, `jetski_id` and `user_id`.
        self.jetski = JetSki.objects.get(pk=jetski_id)
        self.user = User.objects.get(pk=user_id)

    def check_validity(self):
        # Before the Routine logic is run, Umeboshi can check to make sure that
        # it's still valid. In this case, we will check that the jetski in
        # question is still actually out for rent by that user. (What if they
        # returned it and rented it again, you say? Listen, Skily.biz is an MVP.)
        return self.jetski.out_for_rent and self.jetski.user == self.user

    def run(self):
        # Finally, Umeboshi runs the Routine.  
        self.user.charge(600, currency="USD")
```
There's your Routine. Now, to schedule it:

```python
def rent_jetski(jetki, user):
    jetski.out_for_rent = True
    jetski.user = user
    jetski.save()
    # In your application logic, you run the `schedule` method on your Routine
    # class, scheduling the logic for 30 days from now.
    JetSkiLateFee.schedule(datetime_scheduled=now() + timedelta(days=30), args=[jetski.id, user.id])
```

All done. Umeboshi creates an Event whenever `rent_jetski()` is run, and 30
days thence that Event will be processed.

# Other features

- Event status reflects whether Event is waiting to be run, was run successfully, was cancelled before running (eg if it failed a validity check), or if it failed to run
- Routine scheduling behaviors allow rules like run-once, schedule-once, last-only (cancel any existing Events when one is scheduled)
- Task groups allow scheduling behavior to be applied to multiple Routines within a group

# Config
`UMEBOSHI_SERIALIZER`: Path to custom data serializer 

Example:
```
# In Django setting file

UMEBOSHI_SERIALIZER = "example.path.serializer.CustomSerializer"
```

Create custom serializer class. Serializer must contains `dumps` and `loads` methods
```
# project/example/path/serializer.py

import pickle

class CustomSerializer(object):
    def dumps(self, value):
        return pickle.dumps(value, 2)

    def loads(self, value):
        return pickle.loads(value, fix_imports=True, encoding="latin1")
```

# How to install

Install:

```shell
pip install django-umeboshi
```

And add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "umeboshi",
    ...
]
```

Write your Routines and wrap them in the `@routine` decorator.

```python
@routine()
class UsefulRoutine(object):
    trigger_name = 'useful-routine'
    behavior = TriggerBehavior.SCHEDULE_ONCE

    ...

