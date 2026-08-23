package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Safety net on vanilla Entity.isAlliedTo (SRG: m_7307_).
 *
 * Vanilla 1.20.1 implementation is `this.isAlliedTo(p_20355_.getTeam())` -
 * it dereferences the argument immediately with no null check. Any override
 * chain (Goety's Owned, BoneLord, SkullLord, Cultist, ...) that forwards a
 * null entity to super would therefore crash the whole game here.
 *
 * Intercepting the null argument at the vanilla entry point covers every
 * pass-through caller (Goety classes and any other mod) and is safe: a null
 * entity can never be an ally. Non-null arguments pass through unchanged.
 */
@Mixin(Entity.class)
public class EntityIsAlliedToNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
