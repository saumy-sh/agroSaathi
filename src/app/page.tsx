"use client";

import React, { useState, useRef, useEffect } from "react";
import { Mic, Image as ImageIcon, Send, Languages, X, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const API_BASE = "http://localhost:5000/api";

interface Message {
  role: "user" | "bot";
  content: string;
  type: "text" | "image" | "audio";
  fileUrl?: string;
  englishContent?: string;
}

export default function Home() {
  const [view, setView] = useState<"landing" | "chat">("landing");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [language, setLanguage] = useState("en");
  const [isLoading, setIsLoading] = useState(false);

  // Media States
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const languages = [
    { label: "English", value: "en" },
    { label: "Hindi", value: "hi" },
    { label: "Marathi", value: "mr" },
    { label: "Kannada", value: "kn" },
    { label: "Tamil", value: "ta" },
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartChat = (type: "audio" | "image") => {
    setView("chat");
    setMessages([{
      role: "bot",
      content: `Hello! I'm AgroSaathi. How can I help you today with your ${type}?`,
      type: "text"
    }]);
    if (type === "image") {
      setTimeout(() => fileInputRef.current?.click(), 100);
    } else if (type === "audio") {
      setTimeout(() => startRecording(), 100);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      recordingIntervalRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    }
  };

  const cancelRecording = () => {
    stopRecording();
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingSeconds(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSendMessage = async () => {
    if (isLoading) return;
    if (!inputValue.trim() && !imagePreview && !audioBlob) return;

    const newMessages: Message[] = [];

    if (imagePreview) {
      newMessages.push({
        role: "user",
        content: "Shared an image",
        type: "image",
        fileUrl: imagePreview
      });
    }

    if (audioUrl) {
      newMessages.push({
        role: "user",
        content: "Shared an audio message",
        type: "audio",
        fileUrl: audioUrl
      });
    }

    if (inputValue.trim()) {
      newMessages.push({
        role: "user",
        content: inputValue,
        type: "text"
      });
    }

    const hadTextInput = inputValue.trim().length > 0;
    const hadAudioInput = !!audioBlob;

    setMessages(prev => [...prev, ...newMessages]);
    setIsLoading(true);

    // Build conversation history from past text messages (in English)
    const history = messages
      .filter(m => m.type === "text" && m.englishContent)
      .map(m => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.englishContent!,
      }));

    // Build form data
    const formData = new FormData();
    formData.append("language", language);
    formData.append("conversation_history", JSON.stringify(history));

    if (inputValue.trim()) {
      formData.append("text", inputValue);
    }

    if (audioBlob) {
      formData.append("audio", audioBlob, "recording.webm");
    }

    if (selectedImage) {
      formData.append("image", selectedImage);
    }

    // Clear inputs
    setInputValue("");
    removeImage();
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingSeconds(0);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
      }

      // Add transcribed text message if audio was sent
      if (data.transcribed_text && hadAudioInput) {
        setMessages(prev => [...prev, {
          role: "user",
          content: `(Transcribed) ${data.transcribed_text}`,
          type: "text",
          englishContent: data.english_user_text,
        }]);
      }

      // Tag the user's text message with english content for history
      if (hadTextInput) {
        setMessages(prev => {
          const updated = [...prev];
          // Find the last user text message and add englishContent
          for (let i = updated.length - 1; i >= 0; i--) {
            if (updated[i].role === "user" && updated[i].type === "text" && !updated[i].englishContent) {
              updated[i] = { ...updated[i], englishContent: data.english_user_text };
              break;
            }
          }
          return updated;
        });
      }

      // Add bot text response
      setMessages(prev => [...prev, {
        role: "bot",
        content: data.response_text,
        type: "text",
        englishContent: data.english_response_text,
      }]);

      // Add bot audio response
      if (data.audio_url) {
        setMessages(prev => [...prev, {
          role: "bot",
          content: "Audio response",
          type: "audio",
          fileUrl: `${API_BASE.replace('/api', '')}${data.audio_url}`
        }]);
      }
    } catch (error: any) {
      setMessages(prev => [...prev, {
        role: "bot",
        content: `Error: ${error.message}. Make sure the backend server is running.`,
        type: "text"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-zinc-950 text-zinc-100 font-sans">
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={handleImageSelect}
      />

      {/* Background Decor */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/20 blur-[120px] rounded-full" />
      </div>

      {/* Background gradient (Landing only) */}
      {view === "landing" && (
        <div className="absolute inset-0 z-0 opacity-30 pointer-events-none">
          <div className="w-full h-full bg-gradient-to-br from-emerald-900/40 via-zinc-950 to-cyan-900/40" />
          <div className="absolute inset-0 bg-gradient-to-b from-zinc-950/80 via-zinc-950/20 to-zinc-950" />
        </div>
      )}

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-zinc-950/50 backdrop-blur-xl border-b border-zinc-800/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20 cursor-pointer" onClick={() => setView("landing")}>
            <span className="font-bold text-zinc-950 text-xs">AS</span>
          </div>
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            AgroSaathi
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-zinc-900/50 rounded-full px-3 py-1.5 border border-zinc-800">
            <Languages className="w-4 h-4 text-emerald-400" />
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger
                className="border-none bg-transparent h-auto p-0 text-xs focus:ring-0 shadow-none gap-1 min-w-[80px]"
                size="sm"
              >
                <SelectValue placeholder="Language" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800 text-zinc-100">
                {languages.map(lang => (
                  <SelectItem key={lang.value} value={lang.value} className="focus:bg-emerald-500/10 focus:text-emerald-400">
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </header>

      <main className="relative z-10 pt-20 h-screen flex flex-col">
        {view === "landing" ? (
          <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
            <div className="max-w-2xl animate-in fade-in slide-in-from-bottom-8 duration-1000">
              <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
                Empowering Farmers with <br />
                <span className="bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
                  Intelligent AI
                </span>
              </h1>
              <p className="text-zinc-400 text-lg md:text-xl mb-12 max-w-xl mx-auto leading-relaxed">
                Your direct companion for agricultural advice, crop diagnosis, and market insights.
                Available in your native language.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button
                  onClick={() => handleStartChat("audio")}
                  size="lg"
                  className="h-16 px-8 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-zinc-950 font-semibold gap-3 group transition-all hover:scale-105 active:scale-95 shadow-xl shadow-emerald-500/10"
                >
                  <Mic className="w-6 h-6 group-hover:animate-pulse" />
                  <span className="text-lg">Send Audio</span>
                </Button>

                <Button
                  onClick={() => handleStartChat("image")}
                  variant="outline"
                  size="lg"
                  className="h-16 px-8 rounded-2xl border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-100 font-semibold gap-3 group transition-all hover:scale-105 active:scale-95 backdrop-blur-sm"
                >
                  <ImageIcon className="w-6 h-6 text-emerald-400" />
                  <span className="text-lg">Upload Image</span>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col h-full max-w-4xl mx-auto w-full overflow-hidden">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex animate-in fade-in slide-in-from-bottom-4 duration-500",
                    msg.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl px-5 py-3 shadow-lg flex flex-col gap-2",
                      msg.role === "user"
                        ? "bg-emerald-500 text-zinc-950 font-medium rounded-tr-none"
                        : "bg-zinc-900/80 backdrop-blur-md border border-zinc-800 text-zinc-100 rounded-tl-none"
                    )}
                  >
                    {msg.type === "image" && msg.fileUrl && (
                      <img src={msg.fileUrl} alt="User upload" className="rounded-lg max-w-full h-auto max-h-64 object-cover" />
                    )}
                    {msg.type === "audio" && msg.fileUrl && (
                      <div className="flex items-center gap-2">
                        <audio key={msg.fileUrl} controls preload="auto" className="h-8 max-w-full">
                          <source src={msg.fileUrl} type="audio/mpeg" />
                        </audio>
                      </div>
                    )}
                    {msg.type === "text" && <span className="whitespace-pre-wrap">{msg.content}</span>}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start animate-in fade-in">
                  <div className="bg-zinc-900/80 backdrop-blur-md border border-zinc-800 rounded-2xl rounded-tl-none px-5 py-3 shadow-lg">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6 pb-10">
              {/* Attachment Previews */}
              <div className="flex flex-wrap gap-4 mb-3">
                {imagePreview && (
                  <div className="relative group animate-in zoom-in-50 duration-200">
                    <img src={imagePreview} className="w-20 h-20 rounded-xl object-cover border-2 border-emerald-500 shadow-lg" alt="Preview" />
                    <button
                      onClick={removeImage}
                      className="absolute -top-2 -right-2 bg-zinc-900 text-zinc-100 rounded-full p-1 border border-zinc-700 hover:bg-zinc-800 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {audioUrl && !isRecording && (
                  <div className="flex items-center gap-3 bg-zinc-900/80 backdrop-blur-md border border-zinc-800 px-4 py-2 rounded-2xl animate-in slide-in-from-left-4">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium">Audio Recorded</span>
                    <button
                      onClick={cancelRecording}
                      className="text-zinc-400 hover:text-rose-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Input Bar */}
              <div className={cn(
                "bg-zinc-900/50 backdrop-blur-2xl border p-2 rounded-3xl flex items-center gap-2 transition-all shadow-2xl overflow-hidden",
                isRecording ? "border-rose-500/50 bg-rose-500/5" : "border-zinc-800 focus-within:border-emerald-500/50"
              )}>
                {!isRecording ? (
                  <>
                    <div className="flex gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-zinc-400 hover:text-emerald-400 h-10 w-10 rounded-full"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <ImageIcon className="w-5 h-5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-zinc-400 hover:text-emerald-400 h-10 w-10 rounded-full"
                        onClick={startRecording}
                      >
                        <Mic className="w-5 h-5" />
                      </Button>
                    </div>

                    <input
                      type="text"
                      placeholder="Ask anything about farming..."
                      className="flex-1 bg-transparent border-none outline-none text-zinc-100 placeholder:text-zinc-500 px-2 min-w-0"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                      disabled={isLoading}
                    />

                    <Button
                      onClick={handleSendMessage}
                      size="icon"
                      disabled={isLoading || (!inputValue.trim() && !imagePreview && !audioBlob)}
                      className={cn(
                        "h-10 w-10 rounded-2xl shadow-lg transition-all",
                        (isLoading || (!inputValue.trim() && !imagePreview && !audioBlob))
                          ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                          : "bg-emerald-500 hover:bg-emerald-600 text-zinc-950 shadow-emerald-500/20"
                      )}
                    >
                      {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </Button>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-between px-4 h-10">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="absolute inset-0 bg-rose-500 rounded-full animate-ping opacity-25" />
                        <div className="relative w-3 h-3 bg-rose-500 rounded-full" />
                      </div>
                      <span className="text-rose-400 font-mono font-bold tracking-wider">
                        {formatTime(recordingSeconds)}
                      </span>
                      <span className="text-zinc-400 text-sm hidden sm:inline italic">Recording your question...</span>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        onClick={cancelRecording}
                        variant="ghost"
                        className="text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 px-3 h-8 rounded-full text-xs font-bold"
                      >
                        CANCEL
                      </Button>
                      <Button
                        onClick={stopRecording}
                        className="bg-rose-500 hover:bg-rose-600 text-white px-4 h-8 rounded-full flex items-center gap-2 text-xs font-bold shadow-lg shadow-rose-500/20"
                      >
                        <Square className="w-3 h-3 fill-current" />
                        STOP
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <style jsx global>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
