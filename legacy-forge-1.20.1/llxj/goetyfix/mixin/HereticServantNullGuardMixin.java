package llxj.goetyfix.mixin;

import com.mega.revelationfix.common.entity.cultists.HereticServant;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null-guard for RevelationFix's HereticServant.isAlliedTo (SRG: m_7307_).
 *
 * RevelationFix's HereticServant (the "异教徒" that extends Goety's Heretic)
 * forwards a null entity from HurtByTargetGoal.alertOthers into the
 * isAlliedTo chain, which resolves to Goety's Apostle.isAlliedTo and crashes
 * at Apostle.java:399. Guarding this entry stops the null at the caller side,
 * an extra safety net on top of the Apostle guard.
 *
 * RevelationFix is normally bundled inside GoetyRevelation via JarJar; when
 * it is absent, soft mode skips this mixin with a warning and the game still
 * starts. Returning false for a null argument is safe and correct: a null
 * entity can never be an ally.
 */
@Mixin(HereticServant.class)
public class HereticServantNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
