package llxj.goetyfix.mixin;

import com.Polarice3.Goety.common.entities.hostile.BroodMother;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null-guard for BroodMother.isAlliedTo (SRG: m_7307_).
 *
 * Same crash family as the Owned fix: HurtByTargetGoal.alertOthers can pass a
 * null entity (Goety's summons can reach alertOthers with a cleared/absent
 * getLastHurtByMob), and this override either dereferences the argument
 * directly or forwards it to the unguarded vanilla Entity.isAlliedTo.
 *
 * Returning false for a null argument is safe and correct: a null entity can
 * never be an ally.
 */
@Mixin(BroodMother.class)
public class BroodMotherNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}