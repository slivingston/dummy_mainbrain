#!/usr/bin/env python
"""
dummy_flydra.py

create a dummy mainbrain with arbitrary number of objects, objects are born and killed, and move around.


Originally written by Floris van Breugel;
modifications by Scott Livingston.
2010-2011.
"""


import roslib; roslib.load_manifest('dummy_mainbrain')
import rospy
import ros_flydra.msg as msgs
import geometry_msgs.msg as geometry_msgs

import numpy as np
import time
from optparse import OptionParser

# Globals
verbose_mode = False

class DummyMainbrain:

    def __init__(self, nobjects=5, latency=0.05,
                 birth_rate=0.02, death_rate=0.02,
                 fix_nobj=False):
        self.max_num_objects = nobjects
        self.latency = latency
        if fix_nobj:
            self.prob_birth = 0.
            self.prob_death = 0.
        else:
            self.prob_birth = birth_rate
            self.prob_death = death_rate
        
        self.newest_object = 0
        self.framenumber = 0
        
        # initial fly collection
        if fix_nobj:
            init_objects = nobjects
        else:
            init_objects = np.random.randint(0,self.max_num_objects)
        if verbose_mode:
            print "Generating %d random points..." % init_objects
            print "Latency set to %d" % self.latency
            print "Probability of birth is %.4f" % self.prob_birth
            print "Probability of death is %.4f" % self.prob_death
        self.point_list = []
        for i in range(init_objects):
            self.newest_object = self.newest_object + 1
            self.point_list.append( DummyPoint(self.newest_object) )
        
        # ros stuff
        self.pub = rospy.Publisher("flydra_mainbrain_super_packets", msgs.flydra_mainbrain_super_packet)
        rospy.init_node('dummy_mainbrain', anonymous=True)
        
        print 'dummy mainbrain initialized'
        

    def get_objects(self):
        acquire_stamp = rospy.Time.now()
        self.framenumber = self.framenumber + 1
        time.sleep(self.latency)
        
        birth_check = np.random.random()
        if birth_check < self.prob_birth and len(self.point_list) < self.max_num_objects:
            if verbose_mode:
                print "\nGenerating new object..."
            self.newest_object = self.newest_object+1
            self.point_list.append(DummyPoint(self.newest_object))
            if verbose_mode:
                print "Now %d total objects." % len(self.point_list)

        death_check = np.random.random()
        if death_check < self.prob_death and len(self.point_list) > 1:
            ind_to_kill = np.random.randint(0,len(self.point_list))
            if verbose_mode:
                print "\nKilling object %d (at index %d)..." % (self.point_list[ind_to_kill].get_id(), ind_to_kill)
            del self.point_list[ind_to_kill]

        # package with mainbrain message format
        flydra_objects = []
        for i in range(len(self.point_list)):
            obj_id, position, velocity, posvel_covariance_diagonal = self.point_list[i].get_state()
            flydra_object = msgs.flydra_object(obj_id, geometry_msgs.Point(position[0], position[1], position[2]), geometry_msgs.Vector3(velocity[0], velocity[1], velocity[2]), posvel_covariance_diagonal)
            flydra_objects.append(flydra_object)
        
        framenumber = self.framenumber
        reconstruction_stamp = rospy.Time.now()
        objects = flydra_objects
        flydra_mainbrain_packet = msgs.flydra_mainbrain_packet(framenumber, reconstruction_stamp, acquire_stamp, objects)
        flydra_mainbrain_super_packet = msgs.flydra_mainbrain_super_packet([flydra_mainbrain_packet])
        
        self.pub.publish(flydra_mainbrain_super_packet)
        return flydra_mainbrain_super_packet
        
    def run(self):
        print 'dummy mainbrain running'
        while not rospy.is_shutdown():
            time.sleep(self.latency)
            self.get_objects()

        
class DummyPoint:
    def __init__(self, obj_id):
        # random start position values
        self.x0 = np.random.randn()
        self.y0 = np.random.randn()
        self.z0 = np.random.randn()

        # random amplitude values
        self.xamp = np.random.randn()
        self.yamp = np.random.randn()
        self.zamp = np.random.randn()

        # object ID number
        self.obj_id = obj_id

        if verbose_mode:
            print "DummyPoint %d initialized with\n\t(%.4f, %.4f, %.4f) pose,"\
                "\n\t(%.4f, %.4f, %.4f) amplitudes." % (self.obj_id,
                                                        self.x0, self.y0, self.z0,
                                                        self.xamp, self.yamp, self.zamp)

    def get_id(self):
        """Return this object's ID number.
"""
        return self.obj_id

    def get_state(self):
        theta = time.time() % (2*np.pi)
        x = self.xamp*np.cos( theta ) + self.x0
        xvel = -self.xamp*np.sin( theta )
        y = self.yamp*np.sin( theta ) + self.y0
        yvel = -self.yamp*np.cos( theta )
        z = self.zamp*np.sin( theta/2.3 ) + self.z0
        zvel = -self.zamp/2.3*np.cos( theta/2.3 )   

        position = [x,y,z]
        velocity = [xvel,yvel,zvel]
        posvel_covariance_diagonal = [0 for i in range(6)]
        
        return self.obj_id, position, velocity, posvel_covariance_diagonal

########### run as mainbrain node #############
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-n", "--nobjects", type="int", dest="nobjects", default=5,
                      help="maximum number of objects")
    parser.add_option("-l", "--latency", type="float", dest="latency", default=0.05,
                      help="artifial latency of dummy mainbrain")
    parser.add_option("--birth-rate", type="float", dest="birth_rate", default=0.02,
                      help="probability that a new object is born")
    parser.add_option("--death-rate", type="float", dest="death_rate", default=0.02,
                      help="probability that a new object dies")
    parser.add_option("-f", "--fix-count", action="store_true", dest="fix_nobj", default=False,
                      help="use fixed number of objects (rather than random; note that birth/death rates are ignored in this case).")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose_mode", default=False,
                      help="verbose mode")
    (options, args) = parser.parse_args()

    # Use Verbose mode?
    verbose_mode = options.verbose_mode

    print 'starting dummy mainbrain'
    dummy_mainbrain = DummyMainbrain( nobjects=options.nobjects, 
                                      latency=options.latency, 
                                      birth_rate=options.birth_rate, 
                                      death_rate=options.death_rate,
                                      fix_nobj=options.fix_nobj)
    dummy_mainbrain.run()

