"""
Chat Client with GUI - FINAL VERSION
Includes remote shutdown capability from server
"""

import socket
import threading
import customtkinter as ctk
from datetime import datetime
import platform
import os
import time

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.connected = False
        self.username = ""
        self.enrollment = ""
        self.receiving = False
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Classroom Chat - Student")
        self.root.geometry("600x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.show_login_screen()
    
    def show_login_screen(self):
        """Display login screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = ctk.CTkFrame(self.root)
        login_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(login_frame, text="Classroom Chat", 
                                   font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(30, 40))
        
        # Server IP
        server_label = ctk.CTkLabel(login_frame, text="Server IP Address:", 
                                    font=ctk.CTkFont(size=14))
        server_label.pack(pady=(10, 5))
        
        self.server_entry = ctk.CTkEntry(login_frame, width=350, height=40,
                                         placeholder_text="e.g., 192.168.0.154",
                                         font=ctk.CTkFont(size=14))
        self.server_entry.insert(0, "192.168.0.154")
        self.server_entry.pack(pady=(0, 20))
        
        # Enrollment
        enrollment_label = ctk.CTkLabel(login_frame, text="Enrollment Number:", 
                                       font=ctk.CTkFont(size=14))
        enrollment_label.pack(pady=(10, 5))
        
        self.enrollment_entry = ctk.CTkEntry(login_frame, width=350, height=40,
                                            placeholder_text="e.g., 25STUCHH010001",
                                            font=ctk.CTkFont(size=14))
        self.enrollment_entry.pack(pady=(0, 20))
        
        # Name
        name_label = ctk.CTkLabel(login_frame, text="Your Name (or part of it):", 
                                 font=ctk.CTkFont(size=14))
        name_label.pack(pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(login_frame, width=350, height=40,
                                       placeholder_text="Enter your name",
                                       font=ctk.CTkFont(size=14))
        self.name_entry.pack(pady=(0, 30))
        
        # Status
        self.status_label = ctk.CTkLabel(login_frame, text="", 
                                        font=ctk.CTkFont(size=12),
                                        text_color="gray")
        self.status_label.pack(pady=(10, 20))
        
        # Connect button
        self.connect_button = ctk.CTkButton(login_frame, text="Connect", 
                                           width=200, height=45,
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           command=self.connect_to_server)
        self.connect_button.pack(pady=(10, 20))
        
        # Bind Enter
        self.name_entry.bind("<Return>", lambda e: self.connect_to_server())
    
    def connect_to_server(self):
        """Connect to server"""
        server_ip = self.server_entry.get().strip()
        enrollment = self.enrollment_entry.get().strip()
        name = self.name_entry.get().strip()
        
        if not server_ip or not enrollment or not name:
            self.status_label.configure(text="Please fill in all fields", text_color="red")
            return
        
        self.status_label.configure(text="Connecting...", text_color="yellow")
        self.connect_button.configure(state="disabled")
        
        threading.Thread(target=self.do_connect, args=(server_ip, enrollment, name), daemon=True).start()
    
    def do_connect(self, server_ip, enrollment, name):
        """Connect to server"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((server_ip, 12345))
            
            # Wait for AUTH_REQUEST
            auth_request = self.client_socket.recv(1024).decode('utf-8')
            
            # Send enrollment
            self.client_socket.send(enrollment.encode('utf-8'))
            time.sleep(0.1)
            
            # Send name
            self.client_socket.send(name.encode('utf-8'))
            time.sleep(0.1)
            
            # Wait for response
            response = self.client_socket.recv(1024).decode('utf-8')
            
            if response == "AUTH_SUCCESS":
                self.enrollment = enrollment
                self.username = name
                self.connected = True
                self.client_socket.settimeout(None)
                
                # Show chat
                self.root.after(0, self.show_chat_screen)
                
                # Start receiving
                self.receiving = True
                threading.Thread(target=self.receive_messages, daemon=True).start()
            else:
                error = "Authentication failed"
                if ":" in response:
                    error = response.split(":", 1)[1]
                
                self.client_socket.close()
                self.root.after(0, lambda: self.status_label.configure(
                    text=error, text_color="red"))
                self.root.after(0, lambda: self.connect_button.configure(state="normal"))
                
        except socket.timeout:
            self.root.after(0, lambda: self.status_label.configure(
                text="Connection timeout", text_color="red"))
            self.root.after(0, lambda: self.connect_button.configure(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.configure(
                text=f"Error: {str(e)}", text_color="red"))
            self.root.after(0, lambda: self.connect_button.configure(state="normal"))
    
    def show_chat_screen(self):
        """Show chat interface"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Top bar
        top_frame = ctk.CTkFrame(self.root, height=60)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        user_label = ctk.CTkLabel(top_frame, 
                                  text=f"Connected as: {self.username}",
                                  font=ctk.CTkFont(size=14, weight="bold"))
        user_label.pack(side="left", padx=20, pady=15)
        
        self.status_indicator = ctk.CTkLabel(top_frame, 
                                            text="● Connected",
                                            text_color="green")
        self.status_indicator.pack(side="right", padx=20)
        
        # Chat display
        self.chat_frame = ctk.CTkFrame(self.root)
        self.chat_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.chat_display = ctk.CTkTextbox(self.chat_frame, 
                                          font=ctk.CTkFont(size=13),
                                          wrap="word",
                                          state="disabled")
        self.chat_display.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Configure tags
        self.chat_display.configure(state="normal")
        self.chat_display.tag_config("system", foreground="#FFD700")
        self.chat_display.tag_config("announcement", foreground="#FF4444")
        self.chat_display.tag_config("warning", foreground="#FF6600")
        self.chat_display.configure(state="disabled")
        
        # Input area
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.message_entry = ctk.CTkEntry(input_frame, 
                                         placeholder_text="Type message...",
                                         font=ctk.CTkFont(size=14),
                                         height=40)
        self.message_entry.pack(side="left", expand=True, fill="x", padx=(5, 10), pady=5)
        
        self.send_button = ctk.CTkButton(input_frame, 
                                        text="Send",
                                        width=100,
                                        height=40,
                                        command=self.send_message)
        self.send_button.pack(side="right", padx=(0, 5), pady=5)
        
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.focus()
    
    def send_message(self):
        """Send message"""
        if not self.connected:
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        try:
            self.client_socket.send(message.encode('utf-8'))
            self.message_entry.delete(0, 'end')
        except Exception as e:
            self.display_message("SYSTEM: Failed to send message", "system")
            self.handle_disconnect()

    def get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%I:%M:%S %p")
    
    def receive_messages(self):
        """Receive messages"""
        while self.receiving and self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                # Check for raw shutdown command (sent directly, no timestamp)
                if message.strip().startswith("/shutdown"):
                    parts = message.strip().split()
                    if len(parts) == 2:
                        target_enroll = parts[1]
                        if target_enroll == self.enrollment:
                            self.root.after(0, lambda: self.display_message(
                                "⚠️  SYSTEM: Remote shutdown command received!", "warning"))
                            self.root.after(0, lambda: self.display_message(
                                "⚠️  SYSTEM: System will shutdown in 3 seconds...", "warning"))
                            self.root.after(3000, self.execute_shutdown)
                            continue  # Don't display the raw command
                
                # Display all other messages from server
                self.root.after(0, lambda m=message: self.display_message(m))

            except Exception as e:
                if self.receiving:
                    self.root.after(0, lambda: self.display_message(
                        "SYSTEM: Connection lost", "system"))
                break

        if self.receiving:
            self.root.after(0, self.handle_disconnect)
    
    def display_message(self, message, tag=None):
        """Display message"""
        self.chat_display.configure(state="normal")
        
        if tag is None:
            if "ANNOUNCEMENT:" in message:
                tag = "announcement"
            elif "SYSTEM:" in message:
                tag = "system"
            elif "⚠️" in message:
                tag = "warning"
            else:
                tag = "normal"
        
        self.chat_display.insert("end", message + "\n", tag)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
    
    def handle_disconnect(self):
        """Handle disconnect"""
        self.connected = False
        self.receiving = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if hasattr(self, 'status_indicator'):
            self.status_indicator.configure(text="● Disconnected", text_color="red")
        
        if hasattr(self, 'message_entry'):
            self.message_entry.configure(state="disabled")
        if hasattr(self, 'send_button'):
            self.send_button.configure(state="disabled")
    
    def on_closing(self):
        """Handle window close"""
        self.receiving = False
        self.connected = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        self.root.destroy()

    def execute_shutdown(self):
        """Shut down the system"""
        try:
            self.display_message("SYSTEM: Initiating system shutdown NOW!", "warning")
            self.root.update()  # Force UI update
            time.sleep(0.5)  # Brief pause to show message
            
            os_name = platform.system().lower()
            if "windows" in os_name:
                os.system("shutdown /s /t 1")
            elif "linux" in os_name:
                os.system("sudo shutdown -h now")  # May need password/privileges
            elif "darwin" in os_name:  # macOS
                os.system("sudo shutdown -h now")  # May need password/privileges
            else:
                self.display_message("SYSTEM: Unsupported OS for shutdown", "system")
        except Exception as e:
            self.display_message(f"SYSTEM: Failed to shutdown - {e}", "system")
    
    def run(self):
        """Start app"""
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()