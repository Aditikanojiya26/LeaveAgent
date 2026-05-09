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
    <div className="flex h-screen bg-[#212121] text-white">
      {/* Sidebar */}
      <aside className="w-72 bg-[#171717] border-r border-white/10 flex flex-col p-4">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">{user?.name}</h2>
          <p className="text-sm text-gray-400">Welcome back</p>
        </div>

        <button
          onClick={() => createChatMutation.mutate()}
          disabled={createChatMutation.isPending}
          className="w-full rounded-lg bg-white text-black py-2 mb-3 font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {createChatMutation.isPending ? "Creating chat..." : "+ New Chat"}
        </button>

        <button
          onClick={() => logoutMutation.mutate()}
          className="w-full rounded-lg border border-white/20 py-2 mb-6 text-gray-300 hover:bg-white/10 transition"
        >
          Logout
        </button>

        <h3 className="text-sm font-semibold text-gray-400 mb-3">Your Chats</h3>

        <div className="flex-1 overflow-y-auto space-y-2">
          {chatsQuery.isLoading && (
            <p className="text-sm text-gray-400">Loading chats...</p>
          )}

          {chatsQuery.data?.map((chat) => (
            <button
              key={chat.chat_id}
              onClick={() => setSelectedChatId(chat.chat_id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition truncate ${selectedChatId === chat.chat_id
                ? "bg-[#2f2f2f] text-white"
                : "text-gray-300 hover:bg-white/10"
                }`}
            >
              {chat.thread_id}
            </button>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 border-b border-white/10 flex items-center px-6">
          <h1 className="text-xl font-semibold">Chat</h1>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {!selectedChatId ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              Select a chat or create a new one.
            </div>
          ) : messagesQuery.isLoading ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              Loading messages...
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-5">
              {messages.map((msg, idx) => (
                <div
                  key={msg.id || idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                >
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "user"
                        ? "bg-[#2f2f2f] text-white"
                        : "bg-transparent text-gray-100"
                      }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={bottomRef}></div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-white/10 px-6 py-4">
          <div className="max-w-3xl mx-auto flex items-center gap-3 bg-[#2f2f2f] rounded-2xl px-4 py-3">
            <input
              className="flex-1 bg-transparent outline-none text-white placeholder:text-gray-400"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />

            <button
              onClick={handleSend}
              disabled={sendMessageMutation.isPending}
              className="rounded-xl bg-white text-black px-4 py-2 font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}