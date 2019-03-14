# FUZZLON - a 802.15.4 Random Fuzz

This project generates random valid IEEE 802.15.4 packets and sends them using
ApiMote. It is intended for security auditing.

My setup is to connect a debugger to my target, start the fuzzer, record every
received packet to a log and wait for it to crash. Nothing smart on this front.

To run the fuzzer - tweak the `cfg.py` file, connect an ApiMote and run `./fuzz.py`.
For more details see our [blog post](https://www.enigmatos.com/category/blog/).

P.S. it did crash ;)

