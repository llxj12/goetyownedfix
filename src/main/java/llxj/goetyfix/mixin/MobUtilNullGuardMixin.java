package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Goety 静态工具 MobUtil.illagerAllies(Entity, Entity) 的空值守卫。
 *
 * 该工具直接调用 target.getTeam()，任一参数为 null 都会抛空指针。
 * 多个 Goety 的 isAlliedTo 重写都会走到这里；虽然各重写已有入口守卫，
 * 这里再兜一层，防止其它调用方传入 null。
 *
 * 目标类用字符串指定、remap = false：MobUtil 是 Goety 自己的类，
 * 方法名不会被混淆，运行时保持原样。
 */
@Mixin(targets = "com.Polarice3.Goety.utils.MobUtil", remap = false)
public class MobUtilNullGuardMixin {

    @Inject(method = "illagerAllies", at = @At("HEAD"), cancellable = true)
    private static void goetyownedfix$guardIllagerAllies(Entity self, Entity other, CallbackInfoReturnable<Boolean> cir) {
        if (self == null || other == null) {
            cir.setReturnValue(false);
        }
    }
}