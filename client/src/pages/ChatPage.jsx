import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createChat, getChatMessages, getChats, sendMessage } from "../api/chatApi";
import { logoutUser } from "../api/authApi";
import { useAuth } from "../context/AuthContext";

export default function ChatPage() {
    const queryClient = useQueryClient();
    const { user, setUser } = useAuth();
    const [selectedChatId, setSelectedChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const bottomRef = useRef(null);

    const chatsQuery = useQuery({
        queryKey: ["chats"],
        queryFn: getChats,
    });

    const messagesQuery = useQuery({
        queryKey: ["messages", selectedChatId],
        queryFn: () => getChatMessages(selectedChatId),
        enabled: !!selectedChatId,
    });

    const createChatMutation = useMutation({
        mutationFn: createChat,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["chats"] });
            setSelectedChatId(data.chat_id);
            setMessages([]);
        },
    });

    const sendMessageMutation = useMutation({
        mutationFn: sendMessage,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["messages", selectedChatId] });
        },
    });

    const logoutMutation = useMutation({
        mutationFn: logoutUser,
        onSuccess: () => {
            setUser(null);
        },
    });

    useEffect(() => {
        if (messagesQuery.data) {
            setMessages(messagesQuery.data);
        } else {
            setMessages([]);
        }
    }, [messagesQuery.data, selectedChatId]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userText = input;
        let chatId = selectedChatId;

        // If no chat selected, create new chat first


        // Show user message + temporary bot message immediately
        setMessages((prev) => [
            ...prev,
            {
                id: `temp-user-${Date.now()}`,
                role: "user",
                content: userText,
                temporary: true,
            },
            {
                id: `temp-bot-${Date.now()}`,
                role: "assistant",
                content: "Thinking...",
                temporary: true,
            },
        ]);

        if (!chatId) {
            const data = await createChatMutation.mutateAsync();
            chatId = data.chat_id; // use chat_id if backend returns chat_id
            setSelectedChatId(chatId);
        }

        setInput("");

        sendMessageMutation.mutate({
            chatId: chatId,//we can not use selectChatId as update is not immediate
            message: userText,
        });
    };
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);
    return (
        <div
            style={{
                display: "flex",
                gap: 24,
                padding: 24,
                height: "100vh",   // 🔥 important
            }}
        >
            <aside style={{ width: 280,backgroundColor: "var(--sidebar-bg)",
borderRight: "1px solid var(--border)", }}>
                <h2>{user?.name}</h2>

                <button onClick={() => createChatMutation.mutate()}>
                    New Chat
                </button>

                <button onClick={() => logoutMutation.mutate()}>
                    Logout
                </button>

                <h3>Your Chats</h3>
                {chatsQuery.isLoading && <p>Loading chats...</p>}

                {chatsQuery.data?.map((chat) => (
                    <div key={chat.chat_id} >
                        <button
                            onClick={() => setSelectedChatId(chat.chat_id)}
                            style={{
                                width: "100%",
                                textAlign: "left",
                                padding: "8px 12px",
                                marginBottom: 6,
                                border: "none",
                                cursor: "pointer",

                                backgroundColor:
                                    selectedChatId === chat.chat_id ? "#a611e1" : "transparent",
                            }}
                        >
                            {chat.title} #{chat.chat_id}
                        </button>
                    </div>
                ))}
            </aside>

            <main style={{ flex: 1 }}>
                <h1>Basic Chat</h1>

                <div
                    style={{
                        minHeight: 400,
                        maxHeight: 400,
                        overflowY: "auto",     // enables scroll
                        border: "1px solid #ccc",
                        padding: 16,
                        marginBottom: 16,
                    }}
                >
                    {!selectedChatId ? (
                        <p>Select a chat or create a new one.</p>
                    ) : messagesQuery.isLoading ? (
                        <p>Loading messages...</p>
                    ) : (
                        messages.map((msg, idx) => (
                            <div key={msg.id || idx} style={{ marginBottom: 12 }}>
                                <strong>{msg.role === "user" ? "You" : "Bot"}:</strong> {msg.content}
                            </div>
                        ))
                    )}
                    <div ref={bottomRef}></div>
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                    <input
                        style={{ flex: 1 }}
                        placeholder="Type your message"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}

                    />
                    <button
                        onClick={handleSend}
                        disabled={sendMessageMutation.isPending}
                    >
                        Send
                    </button>
                </div>
            </main>
        </div>
    );
}