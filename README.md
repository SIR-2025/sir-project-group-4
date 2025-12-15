
# Group 4 
In order to run our performance script you need 2 services running:
- redis-server conf/redis/redis.conf
- run-dialogflow-cx

Once you have these 2 services running, you can run:

python demos/performance_scripts/DialogFlowIntentDetection.py

Inside this file you find all the code used in the performance.

We tried to have everything in a single location. 

The different lines from the performance are structured inside different intents.

We have a fallback function to deal with Google API exceptions and we have a function to split long texts, so we could try and synchronize speech and gestures.