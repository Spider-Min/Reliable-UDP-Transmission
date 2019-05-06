from socket import *
from utils import *
import time, struct, sys, random

def sender(send_file_name, recv_address, recv_port, sender_socket):

    sender_window = {} # window for storing packages within current window
    sender_socket.settimeout(0.1) # receiver closes idle connection after 5 seconds
    data_chunks = read_file(send_file_name) # Iterator storing all the data
    seqBase = 0
    nextSeq = seqBase  # initial next sequence number
    done = False
    times = 0

    while True:
        # Send packet
        # check if the window is full or EOF has reached
        if nextSeq <= seqBase + WND_SIZE and not done:
            # make connection if seqNum == 0
            if nextSeq == 0:
                pkt = make_packet(nextSeq, '', flag=START_OPCODE)
            # if pkt is not the first pkt
            else:
                # if reach the end of the file, set done to True
                try:
                    chunk = next(data_chunks)
                except:
                    # print("Reach the end of the file")
                    done = True
                # if it is data packet
                if done == False:
                    pkt = make_packet(nextSeq, chunk, flag=DATA_OPCODE)
                else:# if it is the last packet
                    pkt = make_packet(nextSeq, '', flag=END_OPCODE)
            sender_window[nextSeq] = (time.time(), pkt)
            # print("pipline, transmitting packets: " + str(nextSeq))
            sender_socket.sendto(pkt, (recv_address, recv_port))
            nextSeq += 1

        # Wait for acks
        try:
            # if received acks
            message, address = sender_socket.recvfrom(MAX_SIZE)
            # extracting the contents of the packet, with a method from utils
            csum, rsum, arcNum, flag, data = extract_packet(message)

            # ignore ack packet with invalid checksum
            if csum != rsum:
                continue

            # updata sender state according to ack number
            if arcNum > seqBase:# packet has been received, update seqBase number
                sender_window.pop(seqBase)
                seqBase = arcNum
                times = 0
            elif arcNum == seqBase:# packet not received
                times += 1

            if times == 3: # perform fast retransmission
                # print("3 duplicated arcs received, doing retransmit:" + str(nextSeq))
                sender_socket.sendto(sender_window[arcNum][1], (recv_address, recv_port))

            # if the arcSquNum exceed the total chunkNum, end connection
            if  done and arcNum == nextSeq:
                # print("\n last packet has been received.")
                # print(" end connection")
                sender_socket.close()
                return


        # when no ack received, check time stamp
        except Exception as err:
            # check the oldest send but not arc packet
            if len(sender_window) != 0 and (time.time() - sender_window[seqBase][0] > 0.5):
                # print("timeout, retransmiting:" + str(seqBase))
                sender_socket.sendto(sender_window[seqBase][1], (recv_address, recv_port))


def usage():
    print("Usage: python Server.py Inputfile ReceiverAddress ReceiverPort")
    exit()

def main():
    if len(sys.argv) < 4:
        usage()
        sys.exit(-1)

    start_time = time.clock()
    send_file_name = sys.argv[1]
    recv_address = sys.argv[2]
    recv_port = int(sys.argv[3])

    sender_address = "localhost"
    sender_port = 9995

    #create UDP socket to send file on
    sender_socket = socket(AF_INET, SOCK_DGRAM)
    sender_socket.bind((sender_address, sender_port))

    # print("waiting for file to be sent")
    sender(send_file_name, recv_address, recv_port, sender_socket) # main recv function: yields in-order data

    end_time = time.clock()
    # print("start_time: {}, end_time: {}".format(start_time, end_time))
    # print("Sent: {}.".format(send_file_name))

if __name__ == '__main__':
    main()
