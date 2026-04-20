package com.anxin_hitsz.config.agent;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * ClassName: config
 * Package: com.anxin_hitsz.config.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:10
 * @Version 1.0
 */
@Configuration
public class config {

    @Value("${fastapi.service.url}")
    private String fastapiServiceUrl;

    @Bean
    public WebClient fastapiWebClient() {
        return WebClient.builder()
                .baseUrl(fastapiServiceUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }
}
