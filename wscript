#!/usr/bin/env python

def options(opt):
    # Load the C++ compiler options
    opt.load('compiler_cxx')
def configure(ctx):
    # Check for the C++ compiler
    ctx.load('compiler_cxx')

    # Check for required libraries: gtest and glog
    ctx.check(lib='gtest', uselib_store='GTEST')
    ctx.check(lib='glog', uselib_store='GLOG')
    ctx.check(lib='pthread', uselib_store='PTHREAD')
    

def build(ctx):
    # Build the test program using TDigestTest.cpp
    ctx.program(
        source='TDigestTest.cpp',   # Source file to compile
        target='tdigest_test',      # Output executable name
        use=['GTEST', 'GLOG', 'PTHREAD'],      # Libraries to link with
        cxxflags=['-std=c++11'],    # C++ flags
        includes=['.'],             # Include current directory for headers
    )

# Note: There's no need for an install function unless you're installing binaries.
