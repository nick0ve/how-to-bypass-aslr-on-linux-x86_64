In this article, I'll discuss about the application of the technique described by [Samuel Groß](https://twitter.com/5aelo) in his [Remote iPhone Exploitation Part 2: Bringing Light into the Darkness -- a Remote ASLR Bypass](https://googleprojectzero.blogspot.com/2020/01/remote-iphone-exploitation-part-2.html). 


To show this I'm gonna solve a pwnable challenge from [Buckeye CTF](https://ctf.osucyber.club/).

I'll try to keep the content as beginner friendly as possible, so feel free to skip any section if you feel confident enough and just want to see the conclusion.

# 0. Introduction
<p align="center"><img src="./images/intro-chall-description.png"></p><br/>

I didn't play the CTF, but I got interested in the challenge about 2hrs before the ctf end thanks to [Guray00](https://github.com/Guray00), who was asking for help in [fibonhack](https://twitter.com/fibonhack) discord about some crypto shenanigans. 

I couldn't help him, but I took a look at pwnable challenges, and figured it would be good to pratically apply some knowledge gathered by the reading of a P0 entry and hopefully get that bounty.

## 0.1 The challenge

Thankfully to the author, the zip contains binaries, source code and dockerfile to reproduce the same environment as the remote one.

<p align="center"> <img src="./images/intro-dist-files.png" width="50%"><p/> <br/>

### Initial foothold

Before jumping into the challenge, It's always a good thing to grasp some knowledge about the environment, let's scroll through the files and take some notes.

* jail.cfg set some restrictions, let's not forget about those limits since they might screw up the exploit:
  ```
  time_limit: 300
  cgroup_cpu_ms_per_sec: 100
  cgroup_pids_max: 64
  rlimit_fsize: 2048
  rlimit_nofile: 2048
  cgroup_mem_max: 1073741824
  ```

* From the Dockerfile we can learn some interesting things:
  1. Build and install oatpp 1.2.5, maybe there are useful bugs in this specific version?
     ```Docker
     # Install oatpp
     RUN git clone https://github.com/oatpp/oatpp.git
     RUN cd /oatpp && git checkout 1.2.5 && mkdir build && cd build && cmake .. && make install
     ```
  
  2. It builds the challenge from scratch
     ```docker
     WORKDIR /home/ctf/challenge/src/
     RUN mkdir -p src/build && cd src/build && cmake .. && make
     RUN cp src/build/flag_server-exe src/build/libkylezip.so flag.txt /   home/  ctf/challenge/
     ```
     This might be a problem, so let's copy the distribuited binaries  instead.
     ```docker
     COPY bins/flag_server-exe /home/ctf/challenge/
     COPY bins/libkylezip.so /home/ctf/challenge/
     ```
* And the last thing, check the protections of the binaries provided
  <p align="center"> <img src="./images/source-code-folder.png" width="50%"><br/> <i></i><p/>

### Setup the local environment and poke the application

docker-compose.yml file is provided so it is not hard at all to get a working local environment to poke. For those of you that are not confident with docker here is the list of commands you need to know to poke the challenge locally.

```bash
docker-compose build # Build the image, do this whenever you change something
docker-compose up # start the container
docker-compose down # stop the container

docker ps # list containers
docker exec -it <CONTAINER ID> <COMMAND> # exec COMMAND into the container
```

After doing `docker-compose build` you can execute `docker-compose up` to start the container, and connect to the challenge with `nc 127.0.0.1 9000`
<p align="center"> <img src="./images/source-code-folder.png" width="50%"><br/> <i></i><p/> 


### Source code analysis

<p align="center"> <img src="./images/docker-up-nc.png" ><br/> <i></i><p/> 

After all that's a ctf challenge, so the source code is not as large as a real application, mostly glue code to get an oatpp web server up and running. 

In fact the important files which we are gonna analyze are:
* src/controller/MyController.*
* kylezip/decompress.*
