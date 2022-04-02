# TwitterAPI-Wrapper

## Environment Preperation
<ul>
  <li>Create file called .env in the top folder of the repository</li>
  <li>Define API_KEY and API_SECRET_KEY with your twitter credential as following:<br/>
      API_KEY={your_api_key}
      API_SECRET_KEY={your_secret_api_key}
  </li>
</ul>

## Install dependencies
```bash
pip install -r requirements
```

## Usage
```bash
# you can use the config file called 'config.yaml' to configure you run. then:
from twitter import Twitter

twitter = Twitter()
res = twitter.search_wrapper()
```

```bash
# you can also do it without the config file (more flexible query)
from datetime import timedelta
from twitter import Twitter

twitter = Twitter()
res = twitter.search(
    query="unfollow OR unfriend OR unfollowing OR unfollowed",
    time_window=timedelta(
        days=0, 
        hours=1, 
        minutes=0
    ),
    max_size=138
)
```
