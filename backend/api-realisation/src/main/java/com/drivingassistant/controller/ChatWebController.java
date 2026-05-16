package com.drivingassistant.controller;

import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.service.contract.AiChatService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

@Controller
@RequestMapping("/chat")
public class ChatWebController {

    private final AiChatService chatService;
    private final Path voiceInputDir = Paths.get("data/voice-input");

    public ChatWebController(AiChatService chatService) throws IOException {
        this.chatService = chatService;
        Files.createDirectories(voiceInputDir);
    }

    @GetMapping
    public String chatPage(
            @RequestParam(required = false) String sessionId,
            Model model
    ) {
        List<ChatMessageDto> messages = List.of();
        if (sessionId != null && !sessionId.isBlank()) {
            messages = chatService.getChatHistory(sessionId);
        }
        model.addAttribute("messages", messages);
        model.addAttribute("sessionId", sessionId);
        model.addAttribute("request", new ChatRequestDto(null, "", null));
        return "chat";
    }

    @PostMapping
    public String sendMessage(
            @ModelAttribute("request") ChatRequestDto request,
            @RequestParam(required = false) String sessionId,
            @RequestParam(required = false) String audioFile, // ← голосовой файл (опционально)
            RedirectAttributes redirectAttributes
    ) {
        // Собираем полный запрос: контент + аудио (если есть)
        ChatRequestDto fullRequest = new ChatRequestDto(
                sessionId,
                request.content(),
                audioFile  // ← передаём имя файла, сервис сам разберётся
        );

        var response = chatService.processChatRequest(fullRequest);
        redirectAttributes.addAttribute("sessionId", response.sessionId());
        return "redirect:/chat";
    }

    /** Загрузка голосового файла → возврат taskId */
    @PostMapping("/upload-voice")
    @ResponseBody
    public String uploadVoice(@RequestParam("voice") MultipartFile file) throws IOException {
        String taskId = UUID.randomUUID().toString();
        file.transferTo(voiceInputDir.resolve(taskId + ".wav"));
        return taskId;  // фронтенд получит простой текст: "abc123..."
    }

    /** Отдача готового аудиофайла (опционально, если не хотите делать папку публичной) */
    @GetMapping("/audio/{taskId}")
    @ResponseBody
    public byte[] getVoiceAudio(@PathVariable String taskId) throws IOException {
        Path file = Paths.get("data/voice-output").resolve(taskId + ".wav");
        return Files.exists(file) ? Files.readAllBytes(file) : new byte[0];
    }
}
