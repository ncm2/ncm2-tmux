if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm2_tmux#proc = yarp#py3('ncm2_tmux')

let g:ncm2_tmux#source = get(g:, 'ncm2_tmux#source', {
            \ 'name': 'tmux',
            \ 'enable': $TMUX != '',
            \ 'priority': 4,
            \ 'mark': 'T',
            \ 'on_complete': {c -> 
            \       g:ncm2_tmux#proc.try_notify('on_complete', c)},
            \ 'on_warmup': {_ -> g:ncm2_tmux#proc.jobstart()},
            \ })

func! ncm2_tmux#init()
    call ncm2#register_source(g:ncm2_tmux#source)
endfunc


