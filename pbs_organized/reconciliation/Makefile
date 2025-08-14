all:
	$(MAKE) -C DDigest
	$(MAKE) -C PinSketch
	$(MAKE) -C PBS
	$(MAKE) -C Graphene-Cpp

clean:
	$(MAKE) -C DDigest clean
	$(MAKE) -C PinSketch clean
	$(MAKE) -C PBS clean
	$(MAKE) -C Graphene-Cpp	clean 

perf-ddigest:
	$(MAKE) -C DDigest perf
	
perf-graphene:
	$(MAKE) -C Graphene-Cpp perf

perf-pbs:
	$(MAKE) -C PBS perf

perf-pinsketch:
	$(MAKE) -C PinSketch perf
	
perf:
	$(MAKE) -C DDigest perf
	$(MAKE) -C Graphene-Cpp	perf 
	$(MAKE) -C PBS perf
	$(MAKE) -C PinSketch perf

scripts:
	$(MAKE) -C DDigest scripts
	$(MAKE) -C PinSketch scripts
	$(MAKE) -C PBS scripts
	$(MAKE) -C Graphene-Cpp	scripts

.PHONY: clean perf scripts