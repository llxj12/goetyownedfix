package llxj.goetyfix.mixin;

import com.Polarice3.Goety.common.entities.neutral.Owned;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null-guard for Goety's Owned.isAlliedTo (SRG: m_7307_).
 *
 * Crash chain being fixed:
 *   HurtByTargetGoal.alertOthers() line 95 calls mob.isAlliedTo(this.mob.getLastHurtByMob())
 *   with getLastHurtByMob() == null (Goety clears it in Owned.tick()).
 *   Owned.isAlliedTo(null) with getTrueOwner() == null forwards null to
 *   super.isAlliedTo(null) (Owned.java:186), and vanilla
 *   Entity.isAlliedTo(Entity) dereferences the argument (p.getTeam())
 *   without a null check -> NullPointerException -> game crash.
 *
 * Returning false for a null argument is safe and correct: a null entity
 * can never be an ally.
 */
@Mixin(Owned.class)
public class OwnedNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true, require = 1)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
