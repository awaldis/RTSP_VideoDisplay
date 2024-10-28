# Method code for sending RTSP DESCRIBE request.
# It is intended that this code be incorporated into an RTSPClient object.
import hashlib

def send_rtsp_describe(self):
    try:
        # Prepare the initial RTSP DESCRIBE request
        cseq = 2
        describe_request = f"DESCRIBE {self.remove_credentials_from_url()} RTSP/1.0\r\n"
        describe_request += f"CSeq: {cseq}\r\n"
        describe_request += "User-Agent: Python RTSP Client\r\n"
        describe_request += "Accept: application/sdp\r\n"
        describe_request += "\r\n"
        
        # Send the request to the RTSP server
        self.client_socket.send(describe_request.encode())
        
        # Receive the response from the server
        response = self.client_socket.recv(4096)
        response_str = response.decode()
        print("RTSP Server Response (DESCRIBE):\n")
        print(response_str)
        
        # Extract session ID if available
        self.session_id = None
        for line in response_str.split("\r\n"):
            if line.startswith("Session:"):
                self.session_id = line.split(" ")[1]
                break
        
        # Check if authentication is required (401 Unauthorized)
        if "401 Unauthorized" in response_str:
            self.auth_required = True
            # Extract the realm and nonce from the response
            self.auth_realm = None
            self.auth_nonce = None
            for line in response_str.split("\r\n"):
                if line.startswith("WWW-Authenticate: Digest"):
                    parts = line.split(",")
                    for part in parts:
                        if "realm" in part:
                            self.auth_realm = part.split('"')[1]
                        elif "nonce" in part:
                            self.auth_nonce = part.split('"')[1]
            
            if self.auth_realm and self.auth_nonce and self.username and self.password:
                # Compute the digest response
                ha1 = hashlib.md5(f"{self.username}:{self.auth_realm}:{self.password}".encode()).hexdigest()
                ha2 = hashlib.md5(f"DESCRIBE:{self.remove_credentials_from_url()}".encode()).hexdigest()
                response_digest = hashlib.md5(f"{ha1}:{self.auth_nonce}:{ha2}".encode()).hexdigest()
                
                # Prepare the authenticated DESCRIBE request
                cseq += 1
                describe_request = f"DESCRIBE {self.remove_credentials_from_url()} RTSP/1.0\r\n"
                describe_request += f"CSeq: {cseq}\r\n"
                describe_request += "User-Agent: Python RTSP Client\r\n"
                describe_request += "Accept: application/sdp\r\n"
                describe_request += (
                    f"Authorization: Digest username=\"{self.username}\", realm=\"{self.auth_realm}\", nonce=\"{self.auth_nonce}\", uri=\"{self.remove_credentials_from_url()}\", response=\"{response_digest}\"\r\n"
                )
                describe_request += "\r\n"
                
                # Send the authenticated request to the RTSP server
                self.client_socket.send(describe_request.encode())
                
                # Receive the response from the server
                response = self.client_socket.recv(4096)
                response_str = response.decode()
                print("RTSP Server Response (Authenticated DESCRIBE):\n")
                print(response_str)
                
                # Extract session ID if available
                for line in response_str.split("\r\n"):
                    if line.startswith("Session:"):
                        self.session_id = line.split(" ")[1]
                        break
            else:
                print("Authentication required, but realm/nonce extraction failed or credentials not provided.")
        
    except Exception as e:
        print(f"Error: {e}")
