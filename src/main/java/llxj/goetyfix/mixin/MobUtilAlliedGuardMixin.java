package llxj.goetyfix.mixin;

import com.Polarice3.Goety.utils.MobUtil;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Null guard for the static helper MobUtil.illagerAllies(Entity, Entity).
 *
 * Still present in Goety 3.1.5.1 (alongside the newer MobUtil.areAllies) and it
 * dereferences both arguments without a null check. Several Goety isAlliedTo
 * overrides route through it, so a null argument would NPE inside the helper.
 *
 * Returning false when either argument is null is safe: null can never be an ally.
 */
@Mixin(MobUtil.class)
public class MobUtilAlliedGuardMixin {

    @Inject(method = "illagerAllies", at = @At("HEAD"), cancellable = true)
    private static void goetyfix$nullGuardIllagerAllies(Entity self, Entity other, CallbackInfoReturnable<Boolean> cir) {
        if (self == null || other == null) {
            cir.setReturnValue(false);
        }
    }
}
