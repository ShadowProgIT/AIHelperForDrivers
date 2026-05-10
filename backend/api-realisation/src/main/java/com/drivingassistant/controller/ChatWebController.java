package com.drivingassistant.controller;

import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.service.contract.AiChatService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.List;

@Controller
@RequestMapping("/chat")
public class ChatWebController {

    private final AiChatService chatService;

    public ChatWebController(AiChatService chatService) {
        this.chatService = chatService;
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
            RedirectAttributes redirectAttributes
    ) {
        ChatRequestDto fullRequest = new ChatRequestDto(
                sessionId,
                request.content(),
                request.imageUrl()
        );

        var response = chatService.processChatRequest(fullRequest);

        redirectAttributes.addAttribute("sessionId", response.sessionId());
        return "redirect:/chat";
    }
}
