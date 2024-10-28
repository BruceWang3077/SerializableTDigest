#!/usr/bin/env python

def options(opt):
    opt.load('compiler_cxx')
    opt.load('boost',tooldir=['.waf-tools'])
def configure(ctx):
    ctx.load(['compiler_cxx', 'boost'])
    ctx.check(lib='gtest', uselib_store='GTEST')
    ctx.check(lib='glog', uselib_store='GLOG')
    ctx.check(lib='pthread', uselib_store='PTHREAD')
    ctx.check_boost(lib='system filesystem context thread coroutine')
    ctx.env.LIB_BOOST = ['boost_serialization']

def build(ctx):
    # Build the test program using TDigestTest.cpp
    ctx.program(
        source='TDigestTest.cpp',   # Source file to compile
        target='tdigest_test',      # Output executable name
        use=['GTEST', 'GLOG', 'PTHREAD', 'BOOST'],      # Libraries to link with
        cxxflags=['-std=c++11'],    # C++ flags
        includes=['.'],             # Include current directory for headers
    )
    ctx.program(
        source='sample.cpp',
        target='sample_test',
        use=['GTEST', 'GLOG','PTHREAD','BOOST'],
        cxxflags=['-std=c++11'],    # C++ flags
        includes=['.'],   
    )

# Note: There's no need for an install function unless you're installing binaries.
