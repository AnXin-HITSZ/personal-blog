package com.anxin_hitsz.config.filter;

import com.anxin_hitsz.service.impl.user.account.UserDetailsServiceImpl;
import com.anxin_hitsz.utils.JwtUtils;
import jakarta.annotation.Resource;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/**
 * ClassName: JwtAuthenticationFilter
 * Package: com.anxin_hitsz.config.filter
 * Description:
 *
 * @Author AnXin
 * @Create 2026/5/12 15:58
 * @Version 1.0
 */
@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Resource
    private JwtUtils jwtUtils;

    @Resource
    private UserDetailsServiceImpl userDetailsService; // 注入用户详情服务

    /** 内部服务调用的 API Key（用于 Agent 回调等场景） */
    @Value("${internal.api-key:}")
    private String internalApiKey;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        // ==========================================
        // 步骤 1：检查是否为内部服务调用（X-Internal-Api-Key）
        // ==========================================
        String requestPath = request.getRequestURI();
        String incomingApiKey = request.getHeader("X-Internal-Api-Key");
        if (incomingApiKey != null && !incomingApiKey.isBlank()
                && !internalApiKey.isBlank()
                && internalApiKey.equals(incomingApiKey)) {

            log.info("JWT Filter — [{}] 内部服务认证通过（X-Internal-Api-Key）", requestPath);

            // 内部服务认证：principal 为 "internal_service" 字符串（非 UserDetailsImpl），
            // 因此 Controller 中 authentication.getPrincipal() instanceof UserDetailsImpl
            // 会判定为 false，从而使用请求体中的 userId（由 Agent 传入）
            UsernamePasswordAuthenticationToken internalAuth =
                    new UsernamePasswordAuthenticationToken(
                            "internal_service",
                            null,
                            List.of()
                    );
            internalAuth.setDetails(
                    new WebAuthenticationDetailsSource().buildDetails(request)
            );
            SecurityContextHolder.getContext().setAuthentication(internalAuth);

            filterChain.doFilter(request, response);
            return;
        }

        // ==========================================
        // 步骤 2：从请求头中获取 JWT
        // ==========================================
        String authHeader = request.getHeader("Authorization");
        log.info("JWT Filter — [{}] Authorization: {}", requestPath, authHeader != null ? "Bearer ..." : "null");

        // 检查请求头是否存在，且是否以 "Bearer " 开头
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            // 没有 JWT，直接放行（让后续过滤器处理）
            filterChain.doFilter(request, response);
            return;
        }

        // 提取 JWT（去掉 "Bearer " 前缀）
        String token = authHeader.substring(7);

        // ==========================================
        // 步骤 2：验证 JWT 的合法性
        // ==========================================
        if (!jwtUtils.validateToken(token)) {
            log.warn("JWT Filter — [{}] Token 验证失败（签名错误或已过期）", requestPath);
            filterChain.doFilter(request, response);
            return;
        }

        // ==========================================
        // 步骤 3：从 JWT 中解析用户名
        // ==========================================
        String username = jwtUtils.getUsername(token);

        // ==========================================
        // 步骤 4：检查 Security 上下文是否已有认证信息
        // ==========================================
        // 如果 username 不为空，且 Security 上下文中还没有认证信息
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {

            // ==========================================
            // 步骤 5：从数据库加载用户详情
            // ==========================================
            try {
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);

                // ==========================================
                // 步骤 6：将用户信息设置到 Spring Security 上下文
                // ==========================================
                // 创建认证令牌
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                                userDetails,        // 主体（用户详情）
                                null,               // 凭证（密码，这里不需要，因为已经验证过 JWT 了）
                                userDetails.getAuthorities() // 权限列表
                        );

                // 设置请求详情（IP、Session ID 等）
                authentication.setDetails(
                        new WebAuthenticationDetailsSource().buildDetails(request)
                );

                // 【关键】将认证信息设置到 Security 上下文中
                SecurityContextHolder.getContext().setAuthentication(authentication);
                log.info("JWT Filter — [{}] 用户 [{}] 认证成功", requestPath, username);
            } catch (Exception e) {
                log.error("JWT Filter — [{}] 加载用户 [{}] 失败: {}", requestPath, username, e.getMessage());
            }
        }

        // ==========================================
        // 步骤 7：放行请求
        // ==========================================
        filterChain.doFilter(request, response);
    }
}
