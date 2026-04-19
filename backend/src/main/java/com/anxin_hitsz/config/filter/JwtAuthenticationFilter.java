package com.anxin_hitsz.config.filter;

import com.anxin_hitsz.service.impl.user.account.UserDetailsServiceImpl;
import com.anxin_hitsz.utils.JwtUtils;
import jakarta.annotation.Resource;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * ClassName: JwtAuthenticationFilter
 * Package: com.anxin_hitsz.config.filter
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/19 16:34
 * @Version 1.0
 */
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Resource
    private UserDetailsServiceImpl userDetailsService; // 注入用户详情服务

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        // ==========================================
        // 步骤 1：从请求头中获取 JWT
        // ==========================================
        String authHeader = request.getHeader("Authorization");

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
        if (!JwtUtils.validateToken(token)) {
            // JWT 验证失败（签名错误或已过期），直接放行
            filterChain.doFilter(request, response);
            return;
        }

        // ==========================================
        // 步骤 3：从 JWT 中解析用户名
        // ==========================================
        String username = JwtUtils.getUsername(token);

        // ==========================================
        // 步骤 4：检查 Security 上下文是否已有认证信息
        // ==========================================
        // 如果 username 不为空，且 Security 上下文中还没有认证信息
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {

            // ==========================================
            // 步骤 5：从数据库加载用户详情
            // ==========================================
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
        }

        // ==========================================
        // 步骤 7：放行请求
        // ==========================================
        filterChain.doFilter(request, response);
    }
}
