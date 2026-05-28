package com.farm.backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import org.springframework.security.config.http.SessionCreationPolicy;

@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Autowired
    private JwtFilter jwtFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {

        http
            .csrf(csrf -> csrf.disable())
            .cors(org.springframework.security.config.Customizer.withDefaults())

            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            .authorizeHttpRequests(auth -> auth

                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers(org.springframework.http.HttpMethod.OPTIONS, "/**").permitAll()

                .requestMatchers(HttpMethod.GET, "/api/departments").permitAll()
                .requestMatchers("/api/departments/public").permitAll()
                .requestMatchers("/api/department-status/**").permitAll()
                .requestMatchers("/api/attendance/**").permitAll()
                .requestMatchers("/api/employees").permitAll()
                .requestMatchers("/api/cameras").permitAll()
                .requestMatchers("/api/alerts").permitAll()
                .requestMatchers("/api/upload/**").permitAll()
                .requestMatchers("/uploads/**").permitAll()
                .requestMatchers("/api/alerts/ai-detection").permitAll()
                .requestMatchers("/error").permitAll()
                .requestMatchers("/api/ai/status/**").permitAll()



                .requestMatchers("/api/users/**").authenticated()
                .requestMatchers("/api/manager/**").authenticated()
                .requestMatchers("/api/employees/register-face/**").authenticated()
                .requestMatchers("/api/employees/delete-face/**").authenticated()
                .requestMatchers("/api/employees/me").authenticated()

                // Admin-only endpoints (URL-level enforcement)
                .requestMatchers("/api/employees/approve/**").hasAuthority("ROLE_ADMIN")
                .requestMatchers("/api/face-notifications/**").hasAuthority("ROLE_ADMIN")

                .requestMatchers(HttpMethod.POST,   "/api/departments").hasAuthority("ROLE_ADMIN")
                .requestMatchers(HttpMethod.PUT,    "/api/departments/**").hasAuthority("ROLE_ADMIN")
                .requestMatchers(HttpMethod.DELETE, "/api/departments/**").hasAuthority("ROLE_ADMIN")
                .requestMatchers(HttpMethod.GET,    "/api/departments/**").authenticated()

                .requestMatchers("/api/cameras/**").authenticated()

                .anyRequest().authenticated()
            )

            .exceptionHandling(ex -> ex
                // Retourne 401 (pas 403) quand le token est absent ou invalide
                .authenticationEntryPoint((request, response, authException) -> {
                    response.setStatus(401);
                    response.setContentType("application/json");
                    response.getWriter().write("{\"error\":\"Non authentifié. Veuillez vous reconnecter.\"}");
                })
            )
            .formLogin(form -> form.disable())
            .httpBasic(basic -> basic.disable())

            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public org.springframework.web.cors.CorsConfigurationSource corsConfigurationSource() {
        org.springframework.web.cors.CorsConfiguration configuration = new org.springframework.web.cors.CorsConfiguration();
        configuration.setAllowedOrigins(java.util.List.of("http://localhost:4200"));
        configuration.setAllowedMethods(java.util.List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(java.util.Arrays.asList("*"));
        configuration.setAllowCredentials(true);
        org.springframework.web.cors.UrlBasedCorsConfigurationSource source = new org.springframework.web.cors.UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
