## HTTP Server
### Homework #4 for 'OTUS Python Professional' Course

#### Description
A study project of an HTTP server for getting practical knowledge of concurrency and socket programming. The concurrency was implemented through multithreading, using high-level `concurrent.futures` Python module. Sockets are short-lived and close after response is send. The server can return HTTP responses with the contents of its root directory, which is provided as a command line option.

The detailed requirements for the task with tests are available at https://github.com/s-stupnikov/http-test-suite

#### Starting a server
To start a server from a command line:

`$ python httpd.py -p 4000 -r <root_dir>`

The root dir with serving files may be an absolute (if started with '/') or relative path. In latter case the full path is formed around the current working directory. 

When `-i` flag is used, the server tries to create an `index.html' file after GET request to a subdirectory if it doesn't exist there yet. This file will contain a list of files in a given subdirectory. If this behaviour is undesirable, omit this flag.

`$ python httpd.py -p 4000 -r files -i `

#### Results of load testing

`$ ab -n 50000 -c 100 -r http://localhost:4000/`

<pre>This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        Server-X
Server Hostname:        localhost
Server Port:            4000

Document Path:          /
Document Length:        330 bytes

Concurrency Level:      100
Time taken for tests:   26.904 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      23500000 bytes
HTML transferred:       16500000 bytes
Requests per second:    1858.48 [#/sec] (mean)
Time per request:       53.807 [ms] (mean)
Time per request:       0.538 [ms] (mean, across all concurrent requests)
Transfer rate:          853.01 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       5
Processing:     2   54   5.8     54      80
Waiting:        2   54   5.8     54      80
Total:          7   54   5.8     54      80

Percentage of the requests served within a certain time (ms)
  50%     54
  66%     56
  75%     57
  80%     58
  90%     60
  95%     62
  98%     64
  99%     66
 100%     80 (longest request)</pre>

