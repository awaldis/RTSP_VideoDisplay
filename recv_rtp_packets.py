import socket
import struct

def recv_rtp_packets(rtp_port):
        # Create a socket to listen for RTP packets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', rtp_port))
        sock.settimeout(1.0)  # Set timeout to 1 second to allow KeyboardInterrupt to be handled
        print(f"Listening for RTP packets on port {rtp_port}...")

        while True:
            try:
                # Receive data from the socket
                data, _ = sock.recvfrom(2048)
                
                # Parse the RTP header
                rtp_header = struct.unpack('!BBHII', data[:12])
                sequence_number = rtp_header[2]
                timestamp = rtp_header[3]
#                print(f"SeqNum: {sequence_number} Time: {timestamp} {data[14]}")
                
                # Check if the packet is part of an IDR_W_RADL NAL unit
                nal_unit_header = data[14]
                nal_start_of_frag_unit = (nal_unit_header & 0x80) != 0  # (MSB)
                nal_unit_type = nal_unit_header & 0x3F  # (lower 6 bits)

                # IDR_W_RADL NAL unit type is typically 19 in HEVC
                if nal_start_of_frag_unit and nal_unit_type == 19:
                    print(f"IDR_W_RADL start packet received with timestamp: {timestamp}")

            except socket.timeout:
                # Timeout occurred, continue to allow handling of KeyboardInterrupt
                continue
            except KeyboardInterrupt:
                print("Stopped listening.")
                break
            except Exception as e:
                print(f"Error: {e}")

