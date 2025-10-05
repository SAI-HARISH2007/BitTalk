"""
Chat Server - CLEAN VERSION
Shows all messages in terminal + admin commands
"""

import socket
import threading
import time
from datetime import datetime
from student_data import authenticate_student

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.running = True
        
    def start(self):
        """Start the chat server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            print("=" * 60)
            print("CLASSROOM CHAT SERVER")
            print("=" * 60)
            print(f"Server running on {self.host}:{self.port}")
            print("Type /help for commands")
            print("=" * 60)
            print()
            
            # Start admin console
            admin_thread = threading.Thread(target=self.admin_console, daemon=True)
            admin_thread.start()
            
            # Accept connections
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                    client_thread.daemon = True
                    client_thread.start()
                except OSError:
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def handle_client(self, client_socket, address):
        """Handle individual client"""
        username = None
        enrollment = None
        
        try:
            # Send AUTH_REQUEST
            client_socket.send("AUTH_REQUEST".encode('utf-8'))
            time.sleep(0.1)
            
            # Receive enrollment
            enrollment = client_socket.recv(1024).decode('utf-8').strip()
            if not enrollment:
                client_socket.close()
                return
            
            # Receive name
            name = client_socket.recv(1024).decode('utf-8').strip()
            if not name:
                client_socket.close()
                return
            
            # Authenticate
            is_valid, result = authenticate_student(enrollment, name)
            
            if is_valid:
                # Success
                client_socket.send("AUTH_SUCCESS".encode('utf-8'))
                time.sleep(0.1)
                
                username = result
                
                # Store client
                with self.clients_lock:
                    self.clients[client_socket] = {
                        'username': username,
                        'enrollment': enrollment,
                        'ip': address[0],
                        'join_time': datetime.now().strftime("%I:%M:%S %p"),
                        'message_count': 0,
                        'muted': False
                    }
                
                # Notify all
                join_msg = f"SYSTEM: {username} has joined the chat"
                self.broadcast(join_msg, None)
                print(f"[{self.get_timestamp()}] {join_msg}")
                
                # Handle messages
                while self.running:
                    try:
                        message = client_socket.recv(1024).decode('utf-8')
                        if not message:
                            break
                        
                        # Check if muted
                        with self.clients_lock:
                            if client_socket in self.clients and self.clients[client_socket]['muted']:
                                client_socket.send("SYSTEM: You are muted.".encode('utf-8'))
                                continue
                            
                            # Increment count
                            if client_socket in self.clients:
                                self.clients[client_socket]['message_count'] += 1
                        
                        # Broadcast to ALL clients (including sender)
                        broadcast_msg = f"{username}: {message}"
                        self.broadcast(broadcast_msg, None)
                        
                        # Show message in server terminal
                        print(f"[{self.get_timestamp()}] {broadcast_msg}")
                        
                    except Exception as e:
                        break
            else:
                # Failed
                error_msg = f"AUTH_FAILED:{result}"
                client_socket.send(error_msg.encode('utf-8'))
                time.sleep(0.1)
                client_socket.close()
                print(f"[{self.get_timestamp()}] Failed login from {address[0]}")
                return
                
        except Exception as e:
            pass
        finally:
            self.remove_client(client_socket, username)
    
    def broadcast(self, message, sender_socket):
        """Broadcast to all clients (including sender if sender_socket is None)"""
        full_message = f"[{self.get_timestamp()}] {message}"
        
        with self.clients_lock:
            disconnected = []
            for client_socket in self.clients:
                if client_socket != sender_socket:
                    try:
                        client_socket.send(full_message.encode('utf-8'))
                    except Exception as e:
                        disconnected.append(client_socket)
            
            for client_socket in disconnected:
                if client_socket in self.clients:
                    del self.clients[client_socket]
    
    def remove_client(self, client_socket, username):
        """Remove client"""
        with self.clients_lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                del self.clients[client_socket]
                
                try:
                    client_socket.close()
                except:
                    pass
                
                leave_msg = f"SYSTEM: {username} has left the chat"
                print(f"[{self.get_timestamp()}] {leave_msg}")
        
        # Broadcast outside lock
        try:
            self.broadcast(leave_msg, None)
        except:
            pass
    
    def admin_console(self):
        """Admin commands"""
        while self.running:
            try:
                command = input().strip()
                
                if command == '/help':
                    self.show_help()
                elif command == '/users':
                    self.show_users()
                elif command.startswith('/kick '):
                    enrollment = command.split(' ', 1)[1]
                    self.kick_user(enrollment)
                elif command.startswith('/mute '):
                    enrollment = command.split(' ', 1)[1]
                    self.mute_user(enrollment)
                elif command.startswith('/unmute '):
                    enrollment = command.split(' ', 1)[1]
                    self.unmute_user(enrollment)
                elif command.startswith('/announce '):
                    message = command.split(' ', 1)[1]
                    self.announce(message)
                elif command == '/stats':
                    self.show_stats()
                elif command == '/clear':
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("=" * 60)
                    print("CLASSROOM CHAT SERVER")
                    print("=" * 60)
                    print(f"Server running on {self.host}:{self.port}")
                    print("Type /help for commands")
                    print("=" * 60)
                    print()
                elif command == '/quit':
                    print("Shutting down...")
                    self.running = False
                    break
                    
            except EOFError:
                break
            except Exception as e:
                print(f"Console error: {e}")
    
    def show_help(self):
        """Show commands"""
        print("\n" + "=" * 60)
        print("ADMIN COMMANDS")
        print("=" * 60)
        print("/users              - List all connected users")
        print("/kick <enrollment>  - Kick a user")
        print("/mute <enrollment>  - Mute a user")
        print("/unmute <enrollment>- Unmute a user")
        print("/announce <message> - Send announcement to all")
        print("/stats              - Show server statistics")
        print("/clear              - Clear terminal screen")
        print("/help               - Show this help")
        print("/quit               - Shutdown server")
        print("=" * 60 + "\n")
    
    def show_users(self):
        """List users"""
        with self.clients_lock:
            if not self.clients:
                print("\nNo users connected.\n")
                return
            
            print("\n" + "=" * 80)
            print(f"CONNECTED USERS ({len(self.clients)})")
            print("=" * 80)
            print(f"{'Name':<30} {'Enrollment':<18} {'IP':<15} {'Msgs':<6} {'Status'}")
            print("-" * 80)
            
            for info in self.clients.values():
                status = "MUTED" if info['muted'] else "ACTIVE"
                print(f"{info['username']:<30} {info['enrollment']:<18} {info['ip']:<15} "
                      f"{info['message_count']:<6} {status}")
            
            print("=" * 80 + "\n")
    
    def kick_user(self, enrollment):
        """Kick user"""
        with self.clients_lock:
            for client_socket, info in list(self.clients.items()):
                if info['enrollment'] == enrollment:
                    username = info['username']
                    try:
                        client_socket.send("SYSTEM: You have been kicked.".encode('utf-8'))
                        time.sleep(0.1)
                        client_socket.close()
                    except:
                        pass
                    
                    del self.clients[client_socket]
                    print(f"[{self.get_timestamp()}] ADMIN: Kicked {username} ({enrollment})\n")
                    
                    kick_msg = f"SYSTEM: {username} was kicked"
                    threading.Thread(target=self.broadcast, args=(kick_msg, None)).start()
                    return
            
            print(f"[{self.get_timestamp()}] User {enrollment} not found.\n")
    
    def mute_user(self, enrollment):
        """Mute user"""
        with self.clients_lock:
            for client_socket, info in self.clients.items():
                if info['enrollment'] == enrollment:
                    info['muted'] = True
                    username = info['username']
                    print(f"[{self.get_timestamp()}] ADMIN: Muted {username}\n")
                    try:
                        client_socket.send("SYSTEM: You have been muted.".encode('utf-8'))
                    except:
                        pass
                    return
            
            print(f"[{self.get_timestamp()}] User {enrollment} not found.\n")
    
    def unmute_user(self, enrollment):
        """Unmute user"""
        with self.clients_lock:
            for client_socket, info in self.clients.items():
                if info['enrollment'] == enrollment:
                    info['muted'] = False
                    username = info['username']
                    print(f"[{self.get_timestamp()}] ADMIN: Unmuted {username}\n")
                    try:
                        client_socket.send("SYSTEM: You have been unmuted.".encode('utf-8'))
                    except:
                        pass
                    return
            
            print(f"[{self.get_timestamp()}] User {enrollment} not found.\n")
    
    def announce(self, message):
        """Send announcement"""
        announcement = f"ANNOUNCEMENT: {message}"
        self.broadcast(announcement, None)
        print(f"[{self.get_timestamp()}] ADMIN: Announcement sent - {message}\n")
    
    def show_stats(self):
        """Show stats"""
        with self.clients_lock:
            total = len(self.clients)
            messages = sum(info['message_count'] for info in self.clients.values())
            muted = sum(1 for info in self.clients.values() if info['muted'])
        
        print("\n" + "=" * 60)
        print("SERVER STATISTICS")
        print("=" * 60)
        print(f"Connected Users: {total}")
        print(f"Muted Users: {muted}")
        print(f"Total Messages: {messages}")
        print("=" * 60 + "\n")
    
    def get_timestamp(self):
        """Get timestamp"""
        return datetime.now().strftime("%I:%M:%S %p")
    
    def shutdown(self):
        """Shutdown server"""
        self.running = False
        
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("Server shutdown complete.")

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()