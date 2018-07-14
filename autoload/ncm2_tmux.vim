if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm2_tmux#proc = yarp#py3('ncm2_tmux')

let g:ncm2_tmux#source = extend(
            \ get(g:, 'ncm2_tmux#source', {}), {
            \ 'name': 'tmux',
            \ 'enable': $TMUX != '',
            \ 'priority': 4,
            \ 'mark': 'T',
            \ 'on_complete': 'ncm2_tmux#on_complete',
            \ 'on_warmup': 'ncm2_tmux#on_warmup',
            \ }, 'keep')

func! ncm2_tmux#init()
    call ncm2#register_source(g:ncm2_tmux#source)
endfunc

func! ncm2_tmux#on_warmup(ctx)
    call g:ncm2_tmux#proc.jobstart()
endfunc

func! ncm2_tmux#on_complete(ctx)
    call g:ncm2_tmux#proc.try_notify('on_complete', a:ctx)
endfunc
