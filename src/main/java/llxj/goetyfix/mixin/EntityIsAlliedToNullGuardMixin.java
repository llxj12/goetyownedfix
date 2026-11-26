package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * 原版兜底：Entity.isAlliedTo(Entity) 收到 null 时直接返回 false。
 *
 * 1.20.1 原版该方法不判空，直接调用 p.getTeam()，因此任何把 null 透传给它的
 * 重写方法都会在调用链末端抛空指针。这个守卫放在原版入口，覆盖所有
 * "先调 super.isAlliedTo(entityIn)" 的写法。
 *
 * 名字使用 intermediary（Fabric 生产环境的运行时名）：
 *   net.minecraft.class_1297      = Entity
 *   method_5722                   = Entity.isAlliedTo(Entity)
 * 这里不生成 refmap，也不启用 mixin AP（Goety 类不在编译类路径上），
 * 所以方法名与描述符必须写成运行时字面名，并配 remap = false。
 */
@Mixin(targets = "net.minecraft.class_1297", remap = false)
public class EntityIsAlliedToNullGuardMixin {

    @Inject(method = "method_5722(Lnet/minecraft/class_1297;)Z", at = @At("HEAD"), cancellable = true)
    private void goetyownedfix$guardNullAlly(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}