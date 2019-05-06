import struct
import time, random
import binascii

DELAY_RANGE = (0.08, 0.120)
PROB_LOSS   = 0.3
PROB_CORR   = 0.3
MAX_SIZE    = 500
DATA_LENGTH = MAX_SIZE - 10
SEQ_MAX     = 0xffffffff
TIMEOUT     = 0.5
WND_SIZE    = 10

 #flags for :
ACK_OPCODE     = 4 #acks
SPECIAL_OPCODE = 3 #case where start packet and end packet are the same
END_OPCODE     = 2 #end packet
DATA_OPCODE    = 1 #every other packet
START_OPCODE   = 0 #start packet




def channel(pkt):
    """
    unreliable channel simulator. Delays, corrupts, and drops UDP packets

    Input  : Packet in the form of a String
    Output : None OR Corrupted Packet OR Self Packet
    Effects: Random Delay Introduced
    """
    def rand_delay():
        # Delay packet for a uniformly random amount of time between 80 and 120ms.
        delay = random.uniform(*DELAY_RANGE)
        time.sleep(delay)

    def corrupt(pkt):
        # corrupt a packet
        #pkt[index] = str(unichr(random.randint(0, 95)))

        index = random.randint(0, len(pkt) - 1)
        newchar = str(unichr(random.randint(0, 95)))
        pkt     = pkt[:index] + newchar + pkt[index + 1:]
        return pkt

    rand_delay() # Delay All the Packets
    if random.random() < PROB_LOSS:
        print "Packet is Dropped"
        return None
    elif random.random() < PROB_CORR:
        pkt = corrupt(pkt)
        print "Packet is Corrupted"
        return pkt
    else:
        return pkt

"""
packet specification:
    1. checksum  (4 bytes)
    2. seqnum    (4 bytes)
    3. flag      (1 byte)
    4. optional  (1 byte)
    4. data       at most (MAX_SIZE - 10) bytes
A single packet will not exceed MAX_SIZE bytes.
"""
def checksum(message):
    """
    Calculate the modular sum of message in 32 bit
    """
    return struct.pack('I',binascii.crc32(message) & 0xffffffff)

def extract_packet(packet):
    """
    extract packet fields from at most MAX_SIZE bytes data.
    """
    #print("I will try to extract the following packet:",str(packet))
    checked_sum  = int(checksum(packet[4:]).encode('hex'),16)
    received_sum = int(packet[:4].encode('hex'), 16) #convert bytes to integers
    seqnum       = int(packet[4:8].encode('hex'), 16)
    flag         = int(packet[8].encode('hex'), 16)
    data         = packet[10:]
    return checked_sum, received_sum, seqnum, flag, data

def make_packet(seqnum, data, flag=0):
    """
    Make a bytes packet from given information
    """
    # 0, 0, 0, 0
    seqnum_prep      = struct.pack('>I',seqnum)
    flag_prep        = struct.pack('B',flag)
    optional_prep    = struct.pack('B',0)
    data_prep        = data
    #data_prep        = struct.pack('s',data)
    packet_content   = seqnum_prep + flag_prep + optional_prep + data_prep
    csum = checksum(packet_content)

    packet_with_csum = csum + packet_content

    #print("len of seqnum:", len(seqnum_prep))
    #print("len of flag:",   len(flag_prep))
    #print("len of data:",   len(data_prep))
    #print("len of csum:",   len(csum))
    #print("len of packet:", len(packet_with_csum))

    return packet_with_csum
    #packet_content  = str(seqnum) + str(flag) + str(data)

def make_ack(seqnum):
    """
    Make an ack packet (Flag = 4)
    """
    return make_packet(seqnum, bytes(), flag=4)

def read_file(filename, chunk_size=DATA_LENGTH):
    """
    Divide the file into chunks of size chunk_size
    """
    with open(filename, 'rb') as fl:
        while True:
            chunk = fl.read(chunk_size)
            if not chunk:
                break
            yield chunk

def timer(f):
    """
    Decorator to compute the time elapsed to perform a fucntion f
	You can use a simpler method to compute the file transfer time in your program if you prefer
    """
    def timed(*args, **kwargs):

        ts = time.time()
        result = f(*args, **kwargs)
        te = time.time()

        print('took: %2.4f sec' % \
          (te-ts))
        return result

    return timed
