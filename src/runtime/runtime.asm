; runtime.asm
; Minimal runtime library for MiniCompiler
; Sprint 5 requirements: RT-1, RT-2, RT-3, RT-4

section .text

; ============================================================
; print_int: Print integer in rdi to stdout
; ============================================================
global print_int
print_int:
    push rbp
    mov rbp, rsp
    sub rsp, 32

    mov rax, rdi
    mov rdi, 10
    mov rsi, rsp
    add rsi, 24
    mov byte [rsi], 0
    dec rsi

    mov rcx, rsi
    mov rbx, 10

.convert_loop:
    xor rdx, rdx
    div rbx
    add dl, '0'
    mov [rsi], dl
    dec rsi
    test rax, rax
    jnz .convert_loop

    inc rsi
    mov rcx, rsi
    mov rdx, rcx
    mov rsi, rcx
    mov rdi, 1
    mov rax, 1

    mov rcx, rsp
    add rcx, 24
    mov rdx, rcx
    sub rdx, rsi

    syscall

    leave
    ret

; ============================================================
; print_string: Print null-terminated string in rdi
; ============================================================
global print_string
print_string:
    push rbp
    mov rbp, rsp

    mov rcx, rdi
    xor rax, rax

.length_loop:
    cmp byte [rcx], 0
    je .done_length
    inc rcx
    inc rax
    jmp .length_loop

.done_length:
    mov rdx, rax
    mov rsi, rdi
    mov rdi, 1
    mov rax, 1
    syscall

    leave
    ret

; ============================================================
; exit: Exit program with status in rdi
; ============================================================
global exit
exit:
    mov rax, 60
    syscall

; ============================================================
; malloc: Simple heap allocation (placeholder)
; ============================================================
global malloc
malloc:
    xor rax, rax
    ret

; ============================================================
; free: Simple heap free (placeholder)
; ============================================================
global free
free:
    ret