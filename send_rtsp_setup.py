# Method code for sending RTSP SETUP request.
# It is intended that this code be incorporated into an RTSPClient object.
import hashlib

def send_rtsp_setup(self):
    try:
        # Prepare the RTSP SETUP request
        cseq = 3
        setup_request = f"SETUP {self.remove_credentials_from_url()}&trackID=1 RTSP/1.0\r\n"
        setup_request += f"CSeq: {cseq}\r\n"
        setup_request += "Transport: RTP/AVP;unicast;client_port=8000-8001\r\n"
        setup_request += "User-Agent: Python RTSP Client\r\n"
        if self.session_id:
            setup_request += f"Session: {self.session_id}\r\n"
        
        # If authentication is required, add the Authorization header
        if self.auth_required and self.auth_realm and self.auth_nonce and self.username and self.password:
            # Compute the digest response
            ha1 = hashlib.md5(f"{self.username}:{self.auth_realm}:{self.password}".encode()).hexdigest()
            ha2 = hashlib.md5(f"SETUP:{self.remove_credentials_from_url()}&trackID=1".encode()).hexdigest()
            response_digest = hashlib.md5(f"{ha1}:{self.auth_nonce}:{ha2}".encode()).hexdigest()
            setup_request += (
                f"Authorization: Digest username=\"{self.username}\", realm=\"{self.auth_realm}\", nonce=\"{self.auth_nonce}\", uri=\"{self.remove_credentials_from_url()}&trackID=1\", response=\"{response_digest}\"\r\n"
            )
        setup_request += "\r\n"
        
        # Send the SETUP request
        self.client_socket.send(setup_request.encode())
        
        # Receive the response from the server
        response = self.client_socket.recv(4096)
        response_str = response.decode()
        print("----RTSP Server Response (SETUP):----\n")
        print(response_str)

        # Extract session ID if available
        for line in response_str.split("\r\n"):
            if line.startswith("Session:"):
                self.session_id = line.split(" ")[1].split(";")[0]                
                print(f"SETUP - Found Session ID: {self.session_id}")
                break

        
    except Exception as e:
        print(f"Error: {e}")
