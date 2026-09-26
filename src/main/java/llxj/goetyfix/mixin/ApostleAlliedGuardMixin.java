package llxj.goetyfix.mixin;

import com.Polarice3.Goety.common.entities.boss.Apostle;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null guard for Apostle.isAlliedTo(Entity).
 *
 * 1.21.1 / NeoForge version of the goetyownedfix patch: the method is no longer
 * SRG-named (m_7307_), NeoForge 1.21.1 runs on Mojang official names, so the
 * injection targets the plain `isAlliedTo` name.
 *
 * Crash chain being fixed:
 *   HurtByTargetGoal.alertOthers() calls mob.isAlliedTo(this.mob.getLastHurtByMob())
 *   with getLastHurtByMob() == null. This Goety override either dereferences the
 *   argument directly or forwards it to the vanilla Entity.isAlliedTo, which
 *   dereferences it as well (no null check) -> NullPointerException while the
 *   entity ticks -> "Ticking entity" crash.
 *
 * Returning false for a null argument is safe and correct: a null entity can
 * never be an ally. Non-null arguments pass through unchanged.
 *
 * Soft mode (mixins.goetyfix.json: required=false, defaultRequire=0) means a
 * future Goety refactor that removes this class only skips the injection with a
 * warning instead of crashing the game.
 */
@Mixin(Apostle.class)
public class ApostleAlliedGuardMixin {

    @Inject(method = "isAlliedTo", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
