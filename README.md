# shorten
This is a simple URL shortener built as a programming test in 2012. It is done in Python and it uses Google App Engine. It may not necessarily be the way I would solve the assignment today, but I want to keep it faithful to the original.

## Instructions
### Problem description
People are frequently posting URLs using services that limit the length of a message, or do for other reasons, such as preventing a URL spanning multiple lines from being split up and word-wrapped by email software, want to shorten lengthy URLs (and http://lol.ca/ts is so much easier to post to Twitter than http://www.laughing-out-loud.com/FelisSilvestrisCatus.aspx).

Your task is to build a user-facing web service that takes a URL and provides a shorter URL, when possible. When resolved, that URL should redirect the user to the original URL.

### Requirements
* Your solution should be written in Python
* The service should have a user-facing web site (but the graphical design won't matter)
* When given a long URL, the service should shorten it and return the shortened URL
* Visiting the shortened URL should redirect the visitor to the long URL
* You should provide source code as well as a link to a running instance of your service
* You do, of course, not need to register a short domain name
* Please include your thoughts on how to deploy your service in a production environment as well as how you would scale it to millions of users

## Solution
The url shortener is available for you to try at [shorten.countcert.com](http://shorten.countcert.com/)

### Implementation details
A couple of things I would like to remark regarding the decisions I took implementing the code:

#### Main goals
Main aims were set to maximise these desired objectives without incurring in unreasonable trade-offs:
- Generate minimal (or just short) urls.
- Be resource-efficient (spatially, computationally, etc.)
- Have a neat code.

##### Highlights
- **64-base coded URLs**: this enables quick and efficient translation of keys and indexes. Divisions of power of 2 numbers are inexpensive operations. 64 bytes (ascii chars) can easily fit in cache L1. If url length was more prioritary more chars (i.e. unicode encoding) could be added to the table.
- **Encoding DB ids**: shorter than fixed length hashes. Ideally the shortest possible encoding (with an autoincremental int, but in Google App Engine is not exactly like this. In any case better than "locking" counters when about to increment them, storing them in DB, etc.).
- **"Best effort" encode caching**: when a url is submitted is checked against a memcache to check if it is there. If it is, the same is served without having to calculate anything or access the DB. We can use this approach as we don't need to save and serve statistics about each stored url. It is much faster than quering for the url and the increment in the key length (under normal circumstances) is negligible in the long run.
- **"Defensive" encode caching** when a key for a url is created, it is automatically inserted into the memcache before it is needed. Tipically this key will be used more or less in a short period of time in the future. Furthermore, this will completely eliminate the need for DB reads to 0 (as long as memcache is not completely full). This is why I log a warning when a DB read occurs. It also prevents most cases of Cache stampedes.
- **Use of Query API vs GQL**: It does not require run-time parsing.
- **Campaign tracking**: There might be people who would not like their site to be encoded the same way everybody else inserting it in the web [i.e. reusing keys for same urls] (in order to track whether the visits come from the link they provided somebody via e-mail/etc. or just a shortened version of the link another user might have shared). I prioritised efficiency over this (non-specified) functionality, so every new copy of the same url is not guaranteed to generate a new key. This tracking could be achieved anyway: just adding to the original url some "get" parameter the owner could track it (e.g. www.example.com/some_page?id=42), even if it could be too "technical" for the average user. I just wanted to remark this decision, as it could affect on potential number of users (in relation to the "scale to millions" part).

#### Testing
- The application is hosted using [Google App Engine](https://en.wikipedia.org/wiki/Google_App_Engine?oldformat=true). You may want to [download the SDK]((https://cloud.google.com/appengine/downloads)) and execute it locally
- **Running test suites**: you just have to go to "/test?name=%s" test_filename_without_extension. E.g. http://shorten.countcert.com/test?name=test_shorten_page and/or  http://shorten.countcert.com/test?name=test_shorten_aux_functions
- **app.yaml** is already set to "threadsafe: no" because the test framework requires it. The application itself is threadsafe.
- This **version of the test framework gaeunit.py** file differs a few lines of code from the original you can download and try at their page, because it has some compatibility issues with newer versions (>1.1.8) of Google App Engine. I will report the bug and solution to ensure it gets fixed.
- **GET/POST methods**. They have been tested using slightly modified versions of the functions. Instead of receiving the parameters via http requests and respones, etc. they use function parameters an return strings. The tested functionality is about the same and the application can remain "standalone" (without requiring you to install additional packages such as `WebTest`).

### Deploying in a production environment:
- Previous steps
    - First of all, before going "public" the DB and the memcache should be warmed up. In this case, for example, it could suffice entering the N most popular sites from Alexa.
    - Under these "working conditions", the application should be profiled with mock usage modelled after expected behaviour, with different loads (including above expected) from different region IPs, etc.
    - Fine-tune the hardware requirements and the application to meet profiling necessities and profile again. Repeat until reliability and satisfaction achieved.
    markdown

- During deployment
    - Reserve a server/instances/whatever solely for the new version. Keep the old (or rest of the service) running in another machine for a while so it could immediately revert changes by modifying who the loadbalancer is pointing at in case of unexpected problems.
    - Ensure there is enough "manpower" available to answer possible support e-mails in reasonable ammount of time. Because, as the service is new, it might produce more requests about their expectations on how to use it, and this experience could shape the potential future relations with the costumers.

- Long-term
    - Deploy the service preferably using different providers from the strongest competitors, so if their service is down their users can be converted when looking for alternatives and landing on the site (these services despite their promises and SLAs do fail from time to time, e.g. Azure this 29th of Feb. or Amazon some time ago).
    - Not bind using propiertary technologies/languages/etc. that are not under our control or difficult to port to another platform in the future, etc.

### Scaling for milions of users:
Keeping a bit more of control of the application on cloud services than the level Google App Engine offers may be desirable at such a big scale. The additional administrative hassle would probably surpass the benefits of the simplified Google App Engine system. In that situation I would consider the following aspects:

- Look for a CDN provider to host all static files, such as CSS, JS, etc. and maybe a default version of the home page.
- Reduce the amount of server calculation to the minimum. I.e. all non-critical computation should be handled on client-side. E.g. the code that calculates how much chars are saved could be done with a simple JS.
- Use Round-robin DNS to distribute petitions among the different load-balancers.
- Operation-specific memcaches. Different memcaches for code generation (save_url) and for url retrieving (get_url), because the need and use patterns are different. Study the feasibility and benefits of compressing or modifying the keys/data of the memcaches.
- Machine learn on load/usage/etc. to prevent (or at least forecast) usage spikes, know the regions, etc. Do the same with errors, abnormal usage, etc.
- Consider the application of database sharding and/or replication. Regarding sharding, some part of the URL code (e.g. the first character for 64 possible machines) could represent the machine that has it's data. This way, smaller databases also provide better response time and the chosen database can be trivially calculated with cost close to 0.
- Profile the application usage and port to faster languages (i.e. C) the most resource-hungry parts of the code that could benefit from a lower level implementation speed boost.
- Make sure to use some "consistent hashing" on memcaches so it keeps being scalable.
- Implement a queue that takes all petitions from load balancers, in case there is a peak to prevent any from getting lost.
- Use ajax to retrieve encoded urls instead of sending forms (to avoid redirections, reloading of elements that need not to change, etc.)
- Limit the amount of petitions per hour/minute/whatever to each IP to prevent abuse.
