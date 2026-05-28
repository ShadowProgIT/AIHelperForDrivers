package com.drivingassistant.controller;

import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.enums.AiModelType;
import com.drivingassistant.service.contract.AiChatService;
import com.drivingassistant.service.contract.VoiceService;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import java.io.IOException;
import java.util.List;

@Controller
@RequestMapping("/chat")
public class ChatWebController {
    private final AiChatService chatService;
    private final VoiceService voiceService;

    public ChatWebController(AiChatService chatService, VoiceService voiceService) {
        this.chatService = chatService;
        this.voiceService = voiceService;
    }

    @GetMapping
    public String chatPage(@RequestParam(required = false) String sessionId, Model model) {
        List<ChatMessageDto> messages = (sessionId != null && !sessionId.isBlank())
                ? chatService.getChatHistory(sessionId) : List.of();
        model.addAttribute("messages", messages);
        model.addAttribute("sessionId", sessionId);

        model.addAttribute("request", new ChatRequestDto(sessionId, "TEXT", "", null, AiModelType.LOCAL));

        return "chat";
    }

    @PostMapping
    public String sendMessage(
            @ModelAttribute("request") ChatRequestDto request,
            RedirectAttributes redirectAttributes) {
        var response = chatService.processChatRequest(request);
        redirectAttributes.addAttribute("sessionId", response.sessionId());
        return "redirect:/chat";
    }

    @PostMapping("/upload-voice")
    @ResponseBody
    public String uploadVoice(@RequestParam("voice") MultipartFile file) throws IOException {
        // Возвращает taskId, который фронтенд подставит в audio_file
        return voiceService.saveInput(file);
    }

    // Отдача готового аудио (если нужно)
    @GetMapping("/audio/{taskId}")
    @ResponseBody
    public ResponseEntity<Resource> getVoiceAudio(@PathVariable String taskId) throws IOException {

        // Проверяем, готов ли файл
        if (!voiceService.isReady(taskId)) {
            return ResponseEntity.status(HttpStatus.ACCEPTED) // 202 — принято, но ещё не готово
                    .body(null);
        }

        try {
            Resource audioResource = voiceService.getResponseAudio(taskId);

            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_TYPE, "audio/wav")
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + taskId + ".wav\"")
                    .header(HttpHeaders.CACHE_CONTROL, "no-cache, no-store, must-revalidate")
                    .body(audioResource);

        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
