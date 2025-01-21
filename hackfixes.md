Random noise in `src/drivers/mo_atmo_nonhydrostatic.f90` on lines:

```
DO jt = 1, SIZE(p_lnd_state(jg)%prog_lnd(nnow_rcf(jg))%t_so_t,4)
    CALL add_random_noise_3d(p_patch(jg)%cells%all, pinit_amplitude, &
                        p_lnd_state(jg)%prog_lnd(nnow_rcf(jg))%t_so_t(:,:,:,jt) )
ENDDO
```

Result with segfault / p_lnd_state is undefined. It only happens when random noise is added.
Random noise added if pinit_seed is not set to 0
Init value of pinit_seed is read from config/run file.

Ensure:
```
&initicon_nml
 pinit_seed                  =                               0   ! seed for perturbation of initial model state. no perturbation by default
```
that the value 0 is used