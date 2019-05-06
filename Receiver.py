from socket import *
from utils import *
import time, struct, sys, random

def recv(file_name, address, port, local_socket):
	receiver_buffer = {} #buffer for storing out of order packets
	local_socket.settimeout(5) #receiver closes idle connection after 5 seconds
	nextseq = -1 #initial next sequence number
	while True:
		try:
			message_orig, address = local_socket.recvfrom(MAX_SIZE)
			#put the message through the simulated channel (look at the included utils.py)
			#output of channel can mean the packet is dropped, delayed, or corrupted
			message = channel(message_orig)

			#case when packet is dropped
			if message is None:
				print("dropped")
				continue

			#extracting the contents of the packet, with a method from utils
			csum, rsum, seqnum, flag, data = extract_packet(message)

			#for the initial packet
			if nextseq == -1:
				#if packet is not corrupted
				if csum == rsum:
					#case when initial packet is sent out of order
					if flag == DATA_OPCODE or flag == END_OPCODE:
						print("out of order seq", seqnum)
						continue

					nextseq = (seqnum + 1) & 0xffffffff
					#else packet is in order
					ack = make_ack(nextseq) #another method from utils
					print("initial seq", seqnum, flag)
					local_socket.sendto(ack, address)
					yield data

					#if initial packet is the last packet
					if flag == SPECIAL_OPCODE:
						break

			#case when packet is corrupted
			elif csum != rsum:
				ack = make_ack(nextseq) #ack the prev packet that was received
				print("corrupted seqnum ", nextseq)
				local_socket.sendto(ack, address)

			#case when packet recieved out of order
			elif seqnum > nextseq:
				#if seqnum received is inside window
				if seqnum < nextseq + WND_SIZE:
					# put the out of order data into buffer
					print("nextseq is ", nextseq, " so put seqnum ", seqnum, " in buffer")
					receiver_buffer[seqnum] = (data, flag)
				ack = make_ack(nextseq)
				local_socket.sendto(ack, address)

			#case when the packet is GOOD!
			elif seqnum == nextseq:
				nextseq = (seqnum + 1) & 0xffffffff
				print("current seqnum", seqnum, flag)
				yield data

				#else, cumulatively ack the buffered packets
				while nextseq in receiver_buffer:
					data, flag = receiver_buffer[nextseq]
					#yield stored data
					yield data

					receiver_buffer.pop(nextseq)
					nextseq = (nextseq + 1) & 0xffffffff

					print("removed seqnum", nextseq - 1, flag)
					print("nextseq is now ", nextseq)

				ack = make_ack(nextseq)
				local_socket.sendto(ack, address)
				if flag == END_OPCODE:
					print("\n last packet received.")
					return

			#everything else has a seqnum lower than basewindow, so ignore

		except Exception as err:
			print('timeout', err)
			break

def usage():
	print("Usage: python Receiver.py Outputfile ReceiverAddress ReceiverPort")
	exit()

def main():
	if len(sys.argv) < 4:
		usage()
		sys.exit(-1)

	start_time = time.clock()
	file_name = sys.argv[1]
	address = sys.argv[2]
	port = int(sys.argv[3])

	#create UDP socket to receive file on
	local_socket = socket(AF_INET, SOCK_DGRAM)
	local_socket.bind((address, port))

	print("waiting for file")
	received = recv(file_name, address, port, local_socket) # main recv function: yields in-order data

	#once data is fully yeilded, output data into a file
	with open(file_name, 'wb+') as dl:
		for data in received:
			dl.write(data)

	end_time = time.clock()
	print("start_time: {}, end_time: {}".format(start_time, end_time))
	print("Received: {}.".format(file_name))

if __name__ == '__main__':
	main()
