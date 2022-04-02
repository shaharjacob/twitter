import os
import time
import json
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta

import yaml
import requests
from click import secho
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get("API_KEY", "")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")
UTC_DIFF_TIME = 3
TWITTER_DELAY = 15
MAX_RESULTS_PER_REQUEST = 100
current_dir = Path(__file__).resolve().parent

class Twitter(object):
    def __init__(self):
        self.token = self.get_token()


    def get_token(self):
        response = requests.post(
            'https://api.twitter.com/oauth2/token', 
            params={
                'grant_type': 'client_credentials',
            }, 
            auth=(API_KEY, API_SECRET_KEY)
        ).json()
        return response.get("access_token", "")
    

    def search_wrapper(self, path: Path = current_dir / 'config.yaml') -> dict:
        with open(path, 'w') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        
        query = []
        query_ = config["query"]
        if query_.get("query_as_string"):
            query = query_.get("query_as_string")
        else:
            if query_.get("must_contains"):
                must_contains = " ".join(query_.get("must_contains"))
                query.append(must_contains)
            if query_.get("must_exclude"):
                must_exclude = f'-{" -".join(query_.get("must_contains"))}'
                query.append(must_exclude)
            if query_.get("contains_at_least_one"):
                contains_at_least_one = " OR ".join(query_.get("contains_at_least_one"))
                query.append(f'({contains_at_least_one})')
            
            query = " ".join(query)
        
        return self.search(
            query=query,
            time_window=timedelta(
                days=config["time_from_now"]["days"], 
                hours=config["time_from_now"]["hours"], 
                minutes=config["time_from_now"]["minutes"]
            ),
            max_size=config["max_results_size"]
        )


    def search(self,
        query: str, # https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query
        time_window: timedelta,
        max_size: int = 0,
        output: Union[str, Path] = 'output.json'
    ) -> dict:

        def dump_tweets(tweets):
            secho(f"Saving results in {output}", fg="blue")
            with open(output, 'w') as f:
                json.dump(tweets, f, indent='\t')

        try:
            # end time should be at least 10 second from the request time (in UTC time)
            end_time = datetime.now() - timedelta(hours=UTC_DIFF_TIME, seconds=TWITTER_DELAY)
            # if using non-research API, timedelta should be < 7 days
            start_time = end_time - time_window
            
            payload = {
                "query": query,
                "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "max_results": MAX_RESULTS_PER_REQUEST,
            }
            payload_as_array = [f"{k}={v}" for k,v in payload.items()]
            payload_as_string = "&".join(payload_as_array)
            
            tweets = []
            number_of_requests = 1
            # https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
            response = requests.get(
                f'https://api.twitter.com/2/tweets/search/recent?{payload_as_string}',
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.token}"
                }
            ).json()
            tweets.extend(response.get("data", []))
            next_token = response.get("meta", {"next_token": ""}).get("next_token")
            while next_token:
                time.sleep(1) # https://developer.twitter.com/en/docs/twitter-api/rate-limits
                secho(f"{len(tweets)},", fg="blue", nl=False)
                response = requests.get(
                    f'https://api.twitter.com/2/tweets/search/recent?{payload_as_string}&next_token={next_token}',
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {self.token}"
                    }
                ).json()
                tweets.extend(response.get("data", []))
                next_token = response.get("meta", {"next_token": ""}).get("next_token")
                number_of_requests += 1
                if max_size > 0 and len(tweets) > max_size:
                    tweets = tweets[:max_size]
                    break
        except Exception as e:
            dump_tweets(tweets)
            secho(f"[ERROR] {e}", fg="red", bold=True)
            exit(1)
        
        dump_tweets(tweets)

        return {
            "number_of_requests": number_of_requests,
            "tweets": tweets
        }


# twitter = Twitter()
# res = twitter.search(
#     query="unfollow OR unfriend OR unfollowing OR unfollowed",
#     time_window=timedelta(
#         days=0, 
#         hours=1, 
#         minutes=0
#     ),
#     max_size=1038
# )
# for tweet in res["tweets"]:
#     print(tweet)
# print(f"number of tweets: {len(res['tweets'])}")
# print(f'number_of_requests: {res["number_of_requests"]}')