frappe.pages['whatsapp-chat'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Inbox',
		single_column: true
	});


    // Add custom CSS
    $('<style>\
        .whatsapp-container {\
            display: flex;\
            height: calc(100vh - 150px);\
            border: 1px solid #e0e0e0;\
            border-radius: 5px;\
            overflow: hidden;\
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;\
        }\
        .sidebar {\
            width: 30%;\
            border-right: 1px solid #e0e0e0;\
            display: flex;\
            flex-direction: column;\
            background-color: #ffffff;\
        }\
        .chat-area {\
            width: 70%;\
            display: flex;\
            flex-direction: column;\
            background-color: #f0f0f0;\
        }\
        .sidebar-header, .chat-header {\
            padding: 10px 15px;\
            background-color: #f0f0f0;\
            border-bottom: 1px solid #e0e0e0;\
            display: flex;\
            justify-content: space-between;\
            align-items: center;\
        }\
        .search-box {\
            padding: 10px;\
            background-color: #f0f0f0;\
        }\
        .search-box input {\
            width: 100%;\
            padding: 8px 12px;\
            border-radius: 20px;\
            border: 1px solid #e0e0e0;\
        }\
        .contact-list {\
            flex: 1;\
            overflow-y: auto;\
        }\
        .contact-item {\
            padding: 10px 15px;\
            border-bottom: 1px solid #f0f0f0;\
            display: flex;\
            align-items: center;\
            cursor: pointer;\
        }\
        .contact-item:hover {\
            background-color: #f5f5f5;\
        }\
        .contact-item.active {\
            background-color: #e9ebeb;\
        }\
        .avatar {\
            width: 45px;\
            height: 45px;\
            border-radius: 50%;\
            background-color: #6c75f5;\
            color: white;\
            display: flex;\
            justify-content: center;\
            align-items: center;\
            margin-right: 15px;\
            font-weight: bold;\
        }\
        .contact-info {\
            flex: 1;\
        }\
        .contact-name {\
            font-weight: bold;\
            margin-bottom: 5px;\
        }\
        .last-message {\
            font-size: 0.8rem;\
            color: #777;\
            white-space: nowrap;\
            overflow: hidden;\
            text-overflow: ellipsis;\
            max-width: 200px;\
        }\
        .message-time {\
            font-size: 0.75rem;\
            color: #999;\
            margin-left: 10px;\
        }\
        .chat-messages {\
            flex: 1;\
            padding: 15px;\
            overflow-y: auto;\
            background-image: url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' viewBox=\'0 0 100 100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z\' fill=\'%23e5e5e5\' fill-opacity=\'0.3\' fill-rule=\'evenodd\'/%3E%3C/svg%3E");\
            display: flex;\
            flex-direction: column;\
        }\
        .message {\
            max-width: 70%;\
            padding: 8px 12px;\
            border-radius: 7px;\
            margin-bottom: 10px;\
            position: relative;\
            word-wrap: break-word;\
        }\
        .message.received {\
            background-color: white;\
            align-self: flex-start;\
            border-top-left-radius: 0;\
        }\
        .message.sent {\
            background-color: #dcf8c6;\
            align-self: flex-end;\
            border-top-right-radius: 0;\
        }\
        .message-input {\
            display: flex;\
            padding: 10px 15px;\
            background-color: #f0f0f0;\
            border-top: 1px solid #e0e0e0;\
            align-items: center; /* Vertically align items */\
        }\
        .message-input input {\
            flex: 1;\
            padding: 10px 15px;\
            border-radius: 20px;\
            border: 1px solid #e0e0e0;\
            margin-right: 10px;\
        }\
        .message-input label {\
            padding: 5px 15px;\
            border-radius: 20px;\
            background-color: #ddd;\
            color: #555;\
            border: none;\
            cursor: pointer;\
            margin-right: 10px;\
            display: inline-block;\
            /* Added styles */\
            line-height: 1;\
            display: flex;\
            align-items: center;\
            justify-content: center;\
        }\
        .message-input label:hover {\
            background-color: #ccc;\
        }\
        .message-input label i {\
            margin-right: 0; /* Remove default icon spacing */\
        }\
        .message-input button {\
            padding: 5px 15px;\
            border-radius: 20px;\
            background-color: #128C7E;\
            color: white;\
            border: none;\
            cursor: pointer;\
        }\
        .message-input button:hover {\
            background-color: #0c6b5e;\
        }\
        .message-time-detail {\
            font-size: 0.7rem;\
            color: #999;\
            text-align: right;\
            margin-top: 3px;\
        }\
        .chat-placeholder {\
            display: flex;\
            flex-direction: column;\
            justify-content: center;\
            align-items: center;\
            height: 100%;\
            color: #888;\
            padding: 20px;\
            text-align: center;\
        }\
        .chat-placeholder i {\
            font-size: 4rem;\
            margin-bottom: 20px;\
            color: #128C7E;\
        }\
        .status-icon {\
            width: 10px;\
            height: 10px;\
            border-radius: 50%;\
            display: inline-block;\
            margin-right: 5px;\
        }\
        .status-online {\
            background-color: #25D366;\
        }\
        .status-offline {\
            background-color: #888;\
        }\
        .tab-buttons {\
            display: flex;\
            border-bottom: 1px solid #e0e0e0;\
        }\
        .tab-button {\
            flex: 1;\
            text-align: center;\
            padding: 10px;\
            cursor: pointer;\
            border-bottom: 3px solid transparent;\
        }\
        .tab-button.active {\
            border-bottom: 3px solid #128C7E;\
            color: #128C7E;\
        }\
        .chat-header-info {\
            display: flex;\
            align-items: center;\
        }\
        .header-actions {\
            display: flex;\
        }\
        .header-action {\
            padding: 0 10px;\
            cursor: pointer;\
            color: #777;\
        }\
        .header-action:hover {\
            color: #128C7E;\
        }\
       .attachment {\
            border: 1px solid #ddd;\
            padding: 5px;\
            margin-top: 5px;\
            border-radius: 5px;\
            background-color: #eee;\
            font-size: 0.8em;\
        }\
        .attachment a {\
            color: #007bff;\
            text-decoration: none;\
        }\
        .attachment-preview {\
            margin-top: 5px;\
            padding: 5px;\
            border: 1px dashed #ccc;\
            border-radius: 5px;\
            display: none; /* Hidden by default */\
        }\
        .attachment-preview img {\
            max-width: 100px;\
            max-height: 100px;\
        }\
        .attachment-preview .file-name {\
            font-size: 0.8em;\
            margin-top: 5px;\
        }\
    </style>').appendTo(page.$title_area);

    // Create the WhatsApp-like structure
    var whatsappContainer = $('<div class="whatsapp-container"></div>').appendTo(page.main);

    // Sidebar
    var sidebar = $('<div class="sidebar"></div>').appendTo(whatsappContainer);

    // Sidebar Header
    var sidebarHeader = $('<div class="sidebar-header"></div>').appendTo(sidebar);
    $('<div class="avatar">D</div>').appendTo(sidebarHeader);
    $('<div class="header-actions">\
        <div class="header-action"><i class="fa fa-comment-alt"></i></div>\
        <div class="header-action"><i class="fa fa-ellipsis-v"></i></div>\
    </div>').appendTo(sidebarHeader);

    // Tab Buttons
    var tabButtons = $('<div class="tab-buttons">\
        <div class="tab-button active">Chats</div>\
        <div class="tab-button">Status</div>\
        <div class="tab-button">Calls</div>\
    </div>').appendTo(sidebar);

    // Search Box
    var searchBox = $('<div class="search-box"><input type="text" placeholder="Search or start new chat"></div>').appendTo(sidebar);

    // Contact List
    var contactList = $('<div class="contact-list"></div>').appendTo(sidebar);

    // Create static contacts
    var contacts = [
        {
            name: "Desire",
            phone: "+2206571734",
            lastMessage: "? Earn by Referring! ? Hey friend! Let's connect!",
            time: "17 Nov, 2024",
            status: "online",
            avatar: "D",
            messages: [
                { text: "? Earn by Referring! ? Hey friend! Let's connect!", time: "11:30 AM", isSent: false },
                { text: "I'd love to hear from you. How's your day going?", time: "11:35 AM", isSent: false },
                { text: "Great to hear from you!", time: "11:40 AM", isSent: true }
            ]
        },
        {
            name: "John Doe",
            phone: "+1234567890",
            lastMessage: "Hey, how are you doing?",
            time: "12:30 PM",
            status: "offline",
            avatar: "J",
            messages: [
                { text: "Hey, how are you doing?", time: "12:30 PM", isSent: false },
                { text: "I'm good, thanks! How about you?", time: "12:35 PM", isSent: true },
                { text: "Doing pretty well. Just wanted to catch up.", time: "12:40 PM", isSent: false }
            ]
        },
        {
            name: "Alice Smith",
            phone: "+1987654321",
            lastMessage: "Did you get the files I sent?",
            time: "10:15 AM",
            status: "online",
            avatar: "A",
            messages: [
                { text: "Hi there! I'm sending over some important documents.", time: "10:00 AM", isSent: false },
                { text: "Thanks, I'll take a look at them.", time: "10:05 AM", isSent: true },
                { text: "Did you get the files I sent?", time: "10:15 AM", isSent: false }
            ]
        },
        {
            name: "Bob Johnson",
            phone: "+1122334455",
            lastMessage: "Meeting at 3 PM tomorrow",
            time: "Yesterday",
            status: "offline",
            avatar: "B",
            messages: [
                { text: "We need to discuss the new project.", time: "Yesterday, 2:30 PM", isSent: false },
                { text: "Sure, when?", time: "Yesterday, 2:35 PM", isSent: true },
                { text: "Meeting at 3 PM tomorrow", time: "Yesterday, 2:40 PM", isSent: false }
            ]
        },
        {
            name: "Emily Wilson",
            phone: "+1563748290",
            lastMessage: "Check out this article I found",
            time: "Monday",
            status: "online",
            avatar: "E",
            messages: [
                { text: "Hi! How's your week going?", time: "Monday, 9:30 AM", isSent: false },
                { text: "Pretty busy with work, but good overall.", time: "Monday, 10:15 AM", isSent: true },
                { text: "Check out this article I found", time: "Monday, 11:20 AM", isSent: false }
            ]
        }
    ];

    // Chat Area
    var chatArea = $('<div class="chat-area"></div>').appendTo(whatsappContainer);

    // Initialize with placeholder
    var chatPlaceholder = $('<div class="chat-placeholder">\
        <i class="fa fa-comments"></i>\
        <h3>Welcome to WhatsApp</h3>\
        <p>Select a chat to start messaging</p>\
    </div>').appendTo(chatArea);

    // Function to add contact to the list
    function addContact(contact, index) {
        var statusClass = contact.status === "online" ? "status-online" : "status-offline";
        var contactItem = $('<div class="contact-item" data-index="' + index + '">\
            <div class="avatar">' + contact.avatar + '</div>\
            <div class="contact-info">\
                <div class="contact-name">' + contact.name + '</div>\
                <div class="last-message">' + contact.lastMessage + '</div>\
            </div>\
            <div class="message-time">' + contact.time + '</div>\
        </div>').appendTo(contactList);

        // Click event
        contactItem.click(function() {
            $('.contact-item').removeClass('active');
            $(this).addClass('active');
            openChat(contacts[$(this).data('index')]);
        });
    }

    // Add all contacts
    $.each(contacts, function(index, contact) {
        addContact(contact, index);
    });

    // Function to open a chat
    function openChat(contact) {
        // Remove placeholder
        chatArea.empty();

        // Create chat header
        var chatHeader = $('<div class="chat-header">\
            <div class="chat-header-info">\
                <div class="avatar">' + contact.avatar + '</div>\
                <div>\
                    <div class="contact-name">' + contact.name + '</div>\
                    <div class="last-message"><span class="status-icon ' + (contact.status === "online" ? "status-online" : "status-offline") + '"></span>' + (contact.status === "online" ? "Online" : "Offline") + '</div>\
                </div>\
            </div>\
            <div class="header-actions">\
                <div class="header-action"><i class="fa fa-search"></i></div>\
                <div class="header-action"><i class="fa fa-paperclip"></i></div>\
                <div class="header-action"><i class="fa fa-ellipsis-v"></i></div>\
            </div>\
        </div>').appendTo(chatArea);

        // Create messages container
        var messagesContainer = $('<div class="chat-messages"></div>').appendTo(chatArea);

        // Add messages
        $.each(contact.messages, function(index, message) {
            var messageClass = message.isSent ? "sent" : "received";
            var messageItem = $('<div class="message ' + messageClass + '">' + message.text + '<div class="message-time-detail">' + message.time + ' ' + (message.isSent ? '✓✓' : '') + '</div></div>');
            messagesContainer.append(messageItem);
        });

        // Create message input
        var messageInput = $('<div class="message-input">\
            <label for="attachmentInput"><i class="fa fa-paperclip"></i></label>\
            <input type="file" id="attachmentInput" style="display:none;">\
            <input type="text" placeholder="Type a message">\
            <button><i class="fa fa-paper-plane"></i> Send</button>\
        </div>').appendTo(chatArea);

          // Add attachment preview area
        var attachmentPreview = $('<div class="attachment-preview"></div>').appendTo(chatArea);

        // Focus on input
        messageInput.find('input[type="text"]').focus();

        let selectedFile = null; // Store the selected file

        // Handle attachment input
        messageInput.find('#attachmentInput').on('change', function(e) {
            selectedFile = e.target.files[0];
            if (selectedFile) {
                console.log("Attachment selected:", selectedFile.name);
                 // Show attachment preview
                attachmentPreview.empty();
                attachmentPreview.css('display', 'block'); // Show the preview area

                if (selectedFile.type.startsWith('image/')) {
                    // For images, display a thumbnail
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        $('<img src="' + e.target.result + '">').appendTo(attachmentPreview);
                        $('<div class="file-name">' + selectedFile.name + '</div>').appendTo(attachmentPreview);
                    }
                    reader.readAsDataURL(selectedFile);
                } else {
                    // For other files, display the file name
                    $('<div class="file-name">' + selectedFile.name + '</div>').appendTo(attachmentPreview);
                }

            } else {
                 attachmentPreview.css('display', 'none');
            }
        });


        // Function to send message
        function sendMessage() {
            var input = messageInput.find('input[type="text"]');
            var message = input.val().trim();

            if (message || selectedFile) {
                var now = new Date();
                var time = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
                let messageItem;

                if (message && selectedFile) {
                     messageItem = $('<div class="message sent">' + message + '<div class="attachment"><a href="#">' + selectedFile.name + '</a></div><div class="message-time-detail">' + time + ' ✓✓</div></div>');
                }
                 else if (message) {
                      messageItem = $('<div class="message sent">' + message + '<div class="message-time-detail">' + time + ' ✓✓</div></div>');
                 } else {
                    messageItem = $('<div class="message sent"><div class="attachment"><a href="#">' + selectedFile.name + '</a></div><div class="message-time-detail">' + time + ' ✓✓</div></div>');
                }
                messagesContainer.append(messageItem);

                // Clear input and reset selected file
                input.val('');
                $('#attachmentInput').val(''); // Clear the file input
                selectedFile = null;
                attachmentPreview.css('display', 'none'); // Hide the preview after sending

                // Scroll to bottom
                messagesContainer.scrollTop(messagesContainer[0].scrollHeight);

                // Add to contact's messages
                contact.messages.push({ text: message, time: time, isSent: true });

                // Update last message in sidebar
                updateContactLastMessage(contacts.indexOf(contact), message, "Just now", true);

                // Simulate reply after delay
                 // Simulate receiving a reply after a delay
                setTimeout(function() {
                    simulateReceiveMessage(contact);
                }, 2000);
            }
        }

        // Handle send button click
        messageInput.find('button').click(sendMessage);

         // Handle Enter key press in the input field
        messageInput.find('input[type="text"]').keypress(function(e) {
            if (e.which === 13) { // 13 is the Enter key code
                sendMessage();
                return false;  // Prevent the default action (e.g., form submission)
            }
        });

        // Function to simulate receiving a message
        function simulateReceiveMessage(contact) {
            var now = new Date();
            var time = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
            var responses = [
                "Okay, I'll check it out.",
                "Sounds good!",
                "Thanks for the update."
            ];
            var randomResponse = responses[Math.floor(Math.random() * responses.length)];

            var messageItem = $('<div class="message received">' + randomResponse + '<div class="message-time-detail">' + time + '</div></div>');
            messagesContainer.append(messageItem);

            // Play sound notification
            playSound();

            // Scroll to bottom
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);

            // Add to contact's messages
            contact.messages.push({ text: randomResponse, time: time, isSent: false });

             // Update last message in sidebar
            updateContactLastMessage(contacts.indexOf(contact), randomResponse, "Just now", false);
        }
    }

    // Function to play sound
    function playSound() {
        var audio = new Audio('http://localhost:84/files/new-message-2-125765.mp3'); // Replace with your sound file URL
        audio.play();
    }

    // Function to update the last message in the contact list
    function updateContactLastMessage(contactIndex, newMessage, newTime, isSent) {
        var contact = contacts[contactIndex];
        if (contact) {
            contact.lastMessage = newMessage;
            contact.time = newTime;

            // Update the contact item in the sidebar
            var contactItem = $('.contact-item[data-index="' + contactIndex + '"]');
            contactItem.find('.last-message').text(newMessage);
            contactItem.find('.message-time').text(newTime);
        }
    }
};
